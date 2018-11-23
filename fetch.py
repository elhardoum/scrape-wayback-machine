"""
Fetchs wayback machine for URLs against a query and uses randomly shuffled user agents list

example URLs.txt

http://web.archive.org/web/*/dog%20and%20cat
http://web.archive.org/web/*/houses
http://web.archive.org/web/*/writing%20blogs
http://web.archive.org/web/*/ultra%20fine
...


OR, just the queries 1 per line:

example URLs.txt

dog and cat
houses
writing blogs
ultra fine
...

example user-agents.txt

Mozilla/5.0 (Amiga; U; AmigaOS 1.3; en; rv:1.8.1.19) Gecko/20081204 SeaMonkey/1.1.14
Mozilla/5.0 (AmigaOS; U; AmigaOS 1.3; en-US; rv:1.8.1.21) Gecko/20090303 SeaMonkey/1.1.15
Mozilla/5.0 (AmigaOS; U; AmigaOS 1.3; en; rv:1.8.1.19) Gecko/20081204 SeaMonkey/1.1.14
...

"""
class fetch_wayback_machine():
    def __init__(self):
        self.args = None
        self._proxy_index = -1
        self.parse_args()

    """
    Parses CLI arguments. Used to assert all arguments are handles correctly.
    """
    def parse_args(self):
        import argparse

        parser = argparse.ArgumentParser()

        # required arguments
        required = parser.add_argument_group('required arguments')
        required.add_argument('-u', '--urls', metavar='', help='URLs to fetch (file path)', type=lambda s: self.file_path_validator(s), required=True)

        # optional arguments
        optional = parser.add_argument_group('optional arguments')
        optional.add_argument('-ua', '--user-agents', metavar='', help='User agents to use (file path)', type=lambda s: self.file_path_validator(s, False), required=False)
        optional.add_argument('-m', '--max-workers', metavar='', help='Max workers to use for threading', type=int, required=False)
        optional.add_argument('-s', '--save-to', metavar='', help='Distination file path', type=str, required=False)
        optional.add_argument('-p', '--proxy', metavar='', help='Proxy address', type=str, required=False)
        optional.add_argument('-pf', '--proxies-file', metavar='', help='Use a list of proxies (file path)', type=lambda s: self.file_path_validator(s, False), required=False)
        optional.add_argument('-l', '--log-errors', metavar='', help='Log errors to a file', type=str, required=False)
        optional.add_argument('-xh', '--exclude-hosts', metavar='', help='Exclude hosts (query-suggested domains)', type=bool, required=False, default=False)

        # parse arguments
        self.args = vars(parser.parse_args())

    """
    Validate file path CLI argument.
    """
    def file_path_validator(self, path, required=True):
        from os.path import exists
        from argparse import ArgumentTypeError

        if not path and not required:
            return

        if not exists( path ):
            raise ArgumentTypeError("%s is an invalid file path" % str(path))

        return path

    """
    Fetches the wayback machine for anchors and hosts
    This is passed to a thread to execute with arguments
    """
    def task_runner(self, args):
        import requests
        from json import loads

        anchors_url = 'http://web.archive.org/__wb/search/anchor?q=%s' % args['query']
        hosts_url = 'http://web.archive.org/__wb/search/host?q=%s' % args['query']
        res = {'query': args['query']}

        kwargs = dict(headers={'User-agent': args['user_agent']})
        if not kwargs['headers']['User-agent']: del kwargs['headers']['User-agent']

        if 'proxies' in args and args['proxies']:
            self._proxy_index+=1

            if self._proxy_index >= len( args['proxies'] ):
                self._proxy_index = 0

            proxy = args['proxies'][ self._proxy_index ]
            kwargs['proxies'] = {'http' + ( 's' if 'https://' in proxy else '' ): proxy}

        try:
            try:
                r = requests.get(anchors_url, **kwargs)
                objects = r.json()

                if objects and len(objects):
                    res['anchors'] = [ x['link'] for x in objects ]
                else:
                    res['anchors'] = []
            except Exception as e:
                res['error'] = str(e)
                return res

            if not self.args['exclude_hosts']:
                try:
                    r = requests.get(hosts_url, **kwargs)
                    objects = r.json()

                    if objects and 'hosts' in objects.keys() and len(objects['hosts']):
                        res['hosts'] = [ x['display_name'] for x in objects['hosts'] ]
                except Exception as e:
                    pass
        except KeyboardInterrupt:
            pass

        return res

    def run(self):
        # first, load the URLs
        from urllib.parse import unquote
        from os.path import basename

        queries = []
        query_urls = {}
        with open( self.args['urls'] ) as f:
            while True:
                raw_url = f.readline().rstrip()
                url = unquote( raw_url )
                if not url: break
                query = basename( url )

                if query:
                    queries.append( query.rstrip() )
                    query_urls[ query.rstrip() ] = raw_url

        if not queries:
            print ( 'No URLs retrieved.' )
            return

        # load user agents

        user_agents = []
        if self.args['user_agents']:
            with open( self.args['user_agents'] ) as f:
                while True:
                    agent = f.readline().rstrip()
                    if not agent: break
                    user_agents.append( agent )

            from random import shuffle
            shuffle( user_agents )
            
        # max workers validate
        self.args['max_workers'] = self.args['max_workers'] if int(self.args['max_workers']) > 0 else 1

        # load proxies

        proxies = []
        if self.args['proxies_file']:
            with open( self.args['proxies_file'] ) as f:
                while True:
                    proxy = f.readline().rstrip()
                    if not proxy: break
                    proxies.append( proxy )

        if not proxies and self.args['proxy']:
            proxies = [ self.args['proxy'] ]

        from concurrent.futures import ThreadPoolExecutor
        from time import sleep
        executor = ThreadPoolExecutor(max_workers=self.args['max_workers'])

        json_obj = {}
        object_lines = []

        try:
            query_list = []
            for query in queries: query_list.append( {'query': query, 'user_agent': user_agents.pop() if user_agents else None, 'proxies': proxies} )
            for res in executor.map(self.task_runner, [x for x in query_list]):
                json_obj[ query_urls[ res['query'] ] ] = res

                if not res:
                    pass
                elif 'error' in res.keys():
                    if not self.args['log_errors']:
                        from sys import stderr
                    else:
                        stderr = open(self.args['log_errors'], 'a')

                    print ( '%s ended with an error: %s' % ( query_urls[ res['query'] ], res['error'] ), file=stderr )
                elif 'hosts' in res.keys() or 'anchors' in res.keys():

                    if 'anchors' in res.keys() and len(res['anchors']):
                        for anchor in res['anchors']: object_lines.append( anchor )

                    if 'hosts' in res.keys() and len(res['hosts']):
                        for host in res['hosts']: object_lines.append( host )
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print ( 'Caught exception: %s' % (e) )

        if not len( json_obj.keys() ):
            return

        if self.args['save_to']:
            from os.path import realpath
            try:
                with open( self.args['save_to'], 'w' ) as f: f.write( '\n'.join( object_lines ) + '\n' )
                print ( 'Saved to %s' % realpath(self.args['save_to']) )                
            except Exception as e:
                print ( 'Saving to %s ended with an error: %s' % ( realpath(self.args['save_to']), str(e) ) )
                print ( '\n'.join( object_lines ) )
        else:
            # just print to stdout
            print ( '\n'.join( object_lines ) )

if '__main__' == __name__:
    app = fetch_wayback_machine()
    app.run()
