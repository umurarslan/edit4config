# Edit4Config

Nokia SROS, Cisco IOS style (parent/child with space indentation) config edit module with add, delete, replace and search function with regex supported. Every line in config text converted to path (parent) and value (line) based on space indent. After this converting process (Config with Parents or CwP) every config line is unique with own parents and editing can be done easily.

---

## Requirements

[Python >= 3.9](https://www.python.org/downloads/)

> For Windows, select the **Add Python 3.x to PATH** checkbox during installation.

---

## Installation

```
pip install edit4config
```

---

## CwP (Config with Parents) Example

***Config Text:***

```
configure
    ...
    card 1
        card-type iom-e
        ...
        mda 1
            mda-type me10-10gb-sfp+
            ...
            no shutdown
            ...
        mda 2
            ...
        ...
    ...
...
```

***CwP List:*** 

```py
[
...
['configure', '    card 1'],
['configure,card 1', '        card-type iom-e'],
['configure,card 1', '        mda 1'],
['configure,card 1,mda 1', '            mda-type me10-10gb-sfp+'],
...
['configure,card 1,mda 1', '            no shutdown'],
...
['configure,card 1', '        mda 2'],
...
]
```

***CwP Text:***

```
...
configure,card 1
configure,card 1,card-type iom-e
configure,card 1,mda 1
configure,card 1,mda 1,mda-type me10-10gb-sfp+
...
configure,card 1,mda 1,no shutdown
...
configure,card 1,mda 2
...
```

---

## Usage

### EditConfig Simple Usage

After CwP converting EditConfig add, delete, replace, search and other methods can be used as below.


> Add-Delete-Replace methods supported regex, multiple match.

> Add-Delete methods supported serial CwP Text lines with newline.

```py
# import EditConfig module
from edit4config import EditConfig

# read config file and get config_text
with open('CONFIG_FILE.txt') as file:
    config_text = file.read()

# define EditConfig object with options e.g. comments, step_space
# comments for Nokia is ('#', 'echo') and for Cisco is ('!')
# step_space for Nokia is 4 and for Cisco is 1
device_cwp = EditConfig(config_text, 4, ('#', 'echo'))

# add "sync-e" before "no shutdown" under configure,card 1,mda 1
device_cwp.add_before_lines(
                            'configure,card 1,mda 1,sync-e',
                            'configure,card 1,mda 1,no shutdown'
                        )

# delete "no shutdown" under configure,card 1,mda 1
device_cwp.delete_serial_lines('configure,card 1,mda 1,no shutdown')

# replace "no shutdown" with "shutdown" under configure,card 1,mda 1
device_cwp.replace_line(
                        'configure,card 1,mda 1,no shutdown',
                        'configure,card 1,mda 1,shutdown'
                    )

# delete "no shutdown" for all card and all mda with regex
device_cwp.delete_serial_lines(
                            'configure,card \d+,mda \d+,no shutdown',
                            regex_match=True, 
                            multiple_match=True
                            )

# after editing done, convert device_cwp object to text file
new_config_text = device_cwp.cwp_to_text()

with open('CONFIG_FILE_NEW.txt', 'w') as file:
    file.write(new_config_text)

```

Another example below for getting CwP and making custom jobs.

```py
# import EditConfig module
from edit4config import EditConfig

# read config file and get config_text
with open('CONFIG_FILE.txt') as file:
    config_text = file.read()

# define EditConfig object with options e.g. comments, step_space
# comments for Nokia is ('#', 'echo') and for Cisco is ('!')
# step_space for Nokia is 4 and for Cisco is 1
device_cwp = EditConfig(config_text, 4, ('#', 'echo'))

# get full cwp-list from EditConfig object with <cwp> variable
device_cwp_list = device_cwp.cwp

# get ntp config from cwp-list and print
for line_path, line_value in device_cwp.cwp:
    if line_path.startswith('configure,system,time,ntp'):
        print(line_value.strip())

```

---

Besides simple usage check other EditConfig methods e.g. cwp_search, cwp_serial_check.



