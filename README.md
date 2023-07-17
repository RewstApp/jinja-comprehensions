# jinja-comprehensions
Jinja2 environments providing support for list/dict comprehensions, set literals/comprehensions, generator expressions, and list/dict spreading.


### Set literals
```jinja
{{ {'set', 'set', 'literal', 'literal'} }}
```
```
{'literal', 'set'}
```

### Comprehensions
```jinja
list: {{ [n // 2 for n in range(10)] }}
set:  {{ {n // 2 for n in range(10)} }}
dict: {{ {n: n // 2 for n in range(10)} }}
```
```
list: [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
set:  {0, 1, 2, 3, 4}
dict: {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3, 8: 4, 9: 4}
```

### Generator expressions
```jinja
{{ (n // 2 for n in range(10)) | join(', ') }}
```
```
0, 0, 1, 1, 2, 2, 3, 3, 4, 4
```

### List/dict spreading
```jinja
{% set stuff = {'b': 98, 'c': 99, 'd': 100} -%}
{{ {'a': 97, **stuff, 'e': 101} }}
{{ [97, *stuff.values(), 101] }}
```
```
{'a': 97, 'b': 98, 'c': 99, 'd': 100, 'e': 101}
[97, 98, 99, 100, 101]
```

Environments are provided for both sync and async contexts, as well as native variants, too.


# Quickstart
```shell
pip install jinja-comprehensions
```

And use a `ComprehensionEnvironment` (or `NativeComprehensionEnvironment`) instead of the vanilla `jinja2.Environment` to compile your templates:
```python
# For rendering to strings
from jinja_comprehensions import ComprehensionEnvironment
jinja_env = ComprehensionEnvironment()

# For rendering to native types
from jinja_comprehensions import NativeComprehensionEnvironment
jinja_env = NativeComprehensionEnvironment()

# For rendering to native types with async enabled
#  (This env avoids some pitfalls with vanilla Jinja2 native envs and Awaitable return values)
from jinja_comprehensions import NoLiteralEvalComprehensionNativeEnvironment
jinja_env = NoLiteralEvalComprehensionNativeEnvironment()
```
