#!/usr/bin/env python

import re
from typing import List
test_cases = '''
navigator.vibrate(500)
;system('/usr/bin/id')
<A HREF="http://www.gohttp://www.google.com/ogle.com/">XSS</A>
/etc/httpd/logs/error_log
onwheel
&#X000003C;
\\x3c
1' ORDER BY 1,2,3--+
/////example.com
etc%2fpasswd%00
'''

patterns = r'''
navigator.vibrate\(\w+\)
;system\('.*?'\)
<A HREF="http://[^/]+http://.+">XSS</A>
/etc/httpd/.*?
on[a-z]+
&#X[0-9A-F]{6,8};
\\x[a-f0-9]{2}
1' (ORDER|UNION|OR|[A-Z]+) [^-]+--\+
//+[a-z\.]+[a-z]
etc%[0-9a-f]+passwd%[0-9a-f]+
'''


def clean(o: List[str]): 
    return list(filter(lambda x: x, map(lambda x: x.strip(),o )))

import random
def format_mod_sec_rule(o):
  o = o.replace("\"", "\\\"")
  o = o.replace("'", "\\'")
  id = random.randint(10000000, 999900000)
  return f'''SecRule ARGS_GET "@rx x='{o}'" "id:{id},phase:2,deny,status:403,severity:2,tag:'hehexd'"'''

def main():
    tc = clean(test_cases.strip().split('\n'))
    p = clean(patterns.strip().split('\n'))

    z = zip(tc, p)
    for o in z:
        try:
          if re.match(o[1], o[0]):
            print('Matched\t', end='')
          else:
            print('Not Matched\t', end='')
        except Exception as e:
          print(e)
        print(o)
        print("\t", format_mod_sec_rule(o[1]))




if __name__ == '__main__':
    main()