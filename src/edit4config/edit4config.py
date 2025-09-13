'''
Nokia SROS, Cisco IOS style (parent/child with space indentation) config edit module with add, delete, replace and search function with regex supported.

Version: 2025.09.14

'''


import re
from dataclasses import dataclass


@dataclass
class EditConfig:
    '''
    Nokia SROS, Cisco IOS style (parent/child with space indentation) config edit module with add, delete, replace and search function with regex supported. 
    Every line in config text converted to path (parent) and value (line) based on space indent.
    After this converting process (Config with Parents or CwP) every config line is unique with own parents and editing can be done easily.
    '''
    config_text: str
    step_space: int
    comment_tuple: tuple = ()
    sep: str = ','
    start_line: str = ''
    end_line: str = ''

    def __post_init__(self):
        if self.start_line and self.end_line:
            self.config_text = EditConfig._get_between_lines(
                self.config_text, self.start_line, self.end_line)

        self.cwp = EditConfig._config_with_parent(
            self.config_text, self.comment_tuple, self.sep)

    @staticmethod
    def _get_between_lines(config_text, start_line, end_line):
        ''' get between two lines text with re.match, e.g. to get only configure - # Finished '''
        config_text_lines = config_text.splitlines()
        start_line_regex = re.compile(start_line)
        end_line_regex = re.compile(end_line)
        start_index = 0
        end_index = 0
        result_list = []
        result_text = ''
        for iline, line in enumerate(config_text_lines):
            if start_line_regex.match(line):
                start_index = iline
            elif start_index and end_line_regex.match(line):
                end_index = iline
                result_list = config_text_lines[start_index:end_index+1]
                result_text += '\n' + '\n'.join(result_list)+'\n'
                break
        return result_text

    @staticmethod
    def _config_with_parent(config_text: str, comment_tuple: tuple = (), sep: str = ',') -> list[list[str]]:
        '''
        Cisco IOS, Nokia SROS style config listed with parent path

        Return list like "[[parent path, line],[parent path_2, line_2]]"

        line : "no shutdown"
        path of line: "configure,card 1,mda 1"
        [['configure,card 1,mda 1', '            no shutdown'],
        ['configure,card 1,mda 1', '            fail-on-error']]

        For Nokia SROS step_space is 4
        For Cisco IOS step_space is 1

        For Nokia SROS comment_tuple = ('#','echo')
        For Cisco IOS comment_tuple = ('!')

        '''
        # check tab character if used instead of space
        if '\t' in config_text:
            raise SystemError(
                'TAB character found in config text, remove TAB characters or replace with whitespace!')

        config_list = [i.rstrip()
                       for i in config_text.splitlines() if i.strip() != '']
        path_dict = {}
        cwp_list = []
        line_path_list = []
        for iline, line in enumerate(config_list):
            # if comment line
            if line.startswith(comment_tuple):
                if line_path_list:
                    cwp_list.append([sep.join(line_path_list), line])
                    continue
                if config_list.index(line)-1 >= 0:
                    before_line_index = config_list.index(line)-1
                    before_line = config_list[before_line_index]
                    if not before_line.startswith(comment_tuple):
                        cwp_list.append([before_line, line])
                        line_path_list = [before_line]
                        continue
                cwp_list.append(['', line])
                continue
            space = len(line) - len(line.lstrip())
            path_dict[space] = line.strip()
            line_path_list = [
                path_dict[key_space] for key_space in sorted(path_dict)
                if key_space < space
            ]
            cwp_list.append([sep.join(line_path_list), line])

            # path_dict delete
            after_n = 1
            while iline != len(config_list) - after_n:
                after_line_index = iline + after_n
                after_line = config_list[after_line_index]
                after_n += 1
                if after_line.startswith(comment_tuple):
                    continue
                after_space = len(after_line) - len(after_line.lstrip())
                if space > after_space:
                    del path_dict[space]
                break

        return cwp_list

    @staticmethod
    def _ec_text_convert(config_text: str, step_space: int, comment_tuple: tuple = (), sep: str = ',') -> list[list[str]]:
        '''
        convert cwp-text to cwp-list
        'configure,card 1,mda 1,no shutdown' -> [['configure, card 1, mda 1', '            no shutdown'], ...]
        '''
        # line_list = [[line.split(',')[:-1], line.split(',')[-1]]
        line_list = config_text.strip().splitlines()
        # convert [['path1a,path1b','value1a'],['path2a,path2b','value2b']]
        line_path_value_list = [
            [sep.join(i.split(sep)[:-1]), i.split(sep)[-1]] for i in line_list]

        result_list = []
        # add space to value by step_space
        for line_list in line_path_value_list:
            space_n = line_list[0].count(sep) + 1
            # for comments
            if line_list[1].startswith(comment_tuple):
                space_n = 0
            #
            value_w_space = (' ' * step_space * space_n)+line_list[1].strip()
            result_list.append([line_list[0], value_w_space])

        return result_list

    @staticmethod
    def cli_convert(config_text: str, comment_tuple: tuple = (), sep: str = ',') -> str:
        '''
        cli config_text convert to cwp-text config, use for testing and check node cwp-text output
        '''
        # convert to cwp
        cwp_direct = EditConfig._config_with_parent(
            config_text, comment_tuple, sep)
        # merge path and value as list
        list_merge = [i[0]+sep+i[1].strip()
                      for i in cwp_direct if i[0].strip() != '']
        # convert merge list to text
        return '\n'.join(list_merge)

    def cwp_update(self):
        ''' cwp update with current config text '''
        current_config_text = '\n'.join([i[1] for i in self.cwp])
        self.cwp = EditConfig._config_with_parent(
            current_config_text, self.comment_tuple, self.sep)

    def cwp_to_text(self) -> str:
        ''' convert cwp to config_text'''
        return '\n'.join([i[1] for i in self.cwp])

    def cwp_search(self, path: str = '', value: str = '', regex=True) -> list[list[str]]:
        """Search in cwp with regex (if regex=True) for path and value, return [[path, value], ...]."""
        path_check = re.compile(
            path).match if regex else lambda s: s.startswith(path)
        value_check = re.compile(
            value).match if regex else lambda s: s.startswith(value.lstrip())

        return [[p, v.lstrip()] for p, v in self.cwp if path_check(p) and value_check(v.lstrip())]

    def cwp_search_capture(self, path: str = '', value: str = '') -> list[list[str]]:
        """Search in cwp with regex for path and value, return [[groups...], ...]."""
        path_regex = re.compile(path)
        value_regex = re.compile(value)
        results = []

        for p, v in self.cwp:
            v2 = v.lstrip()
            m1, m2 = path_regex.match(p), value_regex.match(v2)
            if m1 and m2:
                groups = list(m1.groups()) + list(m2.groups())
                if groups:
                    results.append(groups)

        return results

    def cwp_serial_check(self, path_and_value_text: str) -> bool:
        ''' check serial lines in cwp with cwp-text (multiline,regex) '''
        path_and_value_list = [
            i.strip() for i in path_and_value_text.splitlines() if i.strip() != '']
        # remove left spaces for value and merge with sep
        cwp_text_no_space = [i[0]+self.sep+i[1].lstrip() for i in self.cwp]
        for iline, vline in enumerate(cwp_text_no_space):
            if re.match(fr'{path_and_value_list[0]}', vline):
                part_cwp_text = cwp_text_no_space[iline:iline +
                                                  len(path_and_value_list)]
                if all((re.match(fr'{i}', j) for i, j in zip(path_and_value_list, part_cwp_text))):
                    return True
        return False

    def delete_serial_lines(self, delete_serial_lines: str, regex_match: bool = False, multiple_match: bool = False):
        '''
        delete serial lines
        CASE: partial delete
        '''
        delete_list = EditConfig._ec_text_convert(
            delete_serial_lines, self.step_space, self.comment_tuple, self.sep)

        len_dl = len(delete_list)
        cont = True
        while cont:
            cont = False
            for iline, vline in enumerate(self.cwp):
                # for regex_match
                if (regex_match and re.match(fr'{delete_list[0][0]}', vline[0]) and
                        re.match(fr'{delete_list[0][1]}', vline[1])):
                    cwp_part_list = self.cwp[iline:iline+len_dl]
                    # regex match for every path and config line
                    if (all((re.match(fr'{i[0]}', j[0]) for i, j in zip(delete_list, cwp_part_list))) and
                            all((re.match(fr'{i[1]}', j[1]) for i, j in zip(delete_list, cwp_part_list)))):
                        del self.cwp[iline:iline+len_dl]
                        cont = True
                        # if only single match not continue
                        if not multiple_match:
                            cont = False
                        break
                elif vline == delete_list[0] and self.cwp[iline:iline+len_dl] == delete_list:
                    del self.cwp[iline:iline+len_dl]
                    cont = True
                    # if only single match not continue
                    if not multiple_match:
                        cont = False
                    break

    def delete_between_lines(self, start_with_line: str, end_with_line: str, regex_match: bool = False, multiple_match: bool = False):
        '''
        delete between <start_with_line> and <end_with_line> single line (first match only (non-greedy), start-end included)
        CASE: delete tree/path
        '''
        start_with = EditConfig._ec_text_convert(
            start_with_line, self.step_space, self.comment_tuple, self.sep)[0]
        end_with = EditConfig._ec_text_convert(
            end_with_line, self.step_space, self.comment_tuple, self.sep)[0]

        # for regex_match
        if regex_match:
            cont = True
            while cont:
                cont = False
                start_line = None
                for iline, vline in enumerate(self.cwp):
                    # find start_line if start_line NOT found before
                    if (start_line is None and
                        re.match(fr'{start_with[0]}', vline[0]) and
                            re.match(fr'{start_with[1]}', vline[1])):
                        start_line = iline
                    # find end_line if start_line found before
                    if (start_line is not None and
                        re.match(fr'{end_with[0]}', vline[0]) and
                            re.match(fr'{end_with[1]}', vline[1])):
                        end_line = iline
                        # del between start and end
                        del self.cwp[start_line:end_line+1]
                        # if multiple_match <while> continue
                        if multiple_match:
                            cont = True
                        # exit from for
                        break

        # without regex
        else:
            while start_with in self.cwp:
                # first index
                fi_line = self.cwp.index(start_with)
                # end index after fi
                ei_line = self.cwp[fi_line:].index(end_with)
                # del fi to ei
                del self.cwp[fi_line:(fi_line+ei_line+1)]
                # if no multiple_match exit from <while> or check with while
                if not multiple_match:
                    break

    def add_after_lines(self, add_lines: str, after_lines: str, regex_match: bool = False, multiple_match: bool = False):
        '''
        add <add_lines> (serial lines) after <after_lines> (serial lines)
        CASE: partial add after
        '''
        add_list = EditConfig._ec_text_convert(
            add_lines, self.step_space, self.comment_tuple, self.sep)
        after_list = EditConfig._ec_text_convert(
            after_lines, self.step_space, self.comment_tuple, self.sep)

        len_after = len(after_list)
        # record line for multiple change
        all_after_line_numbers = []

        for iline, vline in enumerate(self.cwp):
            # for regex_match
            if (regex_match and
                re.match(fr'{after_list[0][0]}', vline[0]) and
                    re.match(fr'{after_list[0][1]}', vline[1])):
                cwp_part_list = self.cwp[iline:iline+len_after]

                # regex match for every path and config line
                if (all((re.match(fr'{i[0]}', j[0]) for i, j in zip(after_list, cwp_part_list))) and
                        all((re.match(fr'{i[1]}', j[1]) for i, j in zip(after_list, cwp_part_list)))):
                    insert_line_number = iline + len_after
                    all_after_line_numbers.append(insert_line_number)
                    # if only single match
                    if not multiple_match:
                        break

            elif vline == after_list[0] and self.cwp[iline:iline+len_after] == after_list:
                insert_line_number = iline + len_after
                # record line number
                all_after_line_numbers.append(insert_line_number)
                # if only single match
                if not multiple_match:
                    break

        # every adding change line number
        change_line_number = 0

        for line in all_after_line_numbers:
            # add line number for before changing
            exact_line = line + change_line_number
            self.cwp[exact_line:exact_line] = add_list
            # increase line number with len(add_list)
            change_line_number += len(add_list)

    def add_before_lines(self, add_lines: str, before_lines: str, regex_match: bool = False, multiple_match: bool = False):
        '''
        add <add_lines> (serial lines) before <before_lines> (serial lines)
        CASE: partial add before
        '''
        # convert text to list and add proper step space
        add_list = EditConfig._ec_text_convert(
            add_lines, self.step_space, self.comment_tuple, self.sep)
        before_list = EditConfig._ec_text_convert(
            before_lines, self.step_space, self.comment_tuple, self.sep)

        len_before = len(before_list)
        # record line for multiple change
        all_before_line_numbers = []

        for iline, vline in enumerate(self.cwp):
            # for regex_match
            if (regex_match and
                re.match(fr'{before_list[0][0]}', vline[0]) and
                    re.match(fr'{before_list[0][1]}', vline[1])):
                cwp_part_list = self.cwp[iline:iline+len_before]

                # regex match for every path and config line
                if (all((re.match(fr'{i[0]}', j[0]) for i, j in zip(before_list, cwp_part_list))) and
                        all((re.match(fr'{i[1]}', j[1]) for i, j in zip(before_list, cwp_part_list)))):
                    insert_line_number = iline
                    all_before_line_numbers.append(insert_line_number)
                    # if only single match
                    if not multiple_match:
                        break

            elif vline == before_list[0] and self.cwp[iline:iline+len_before] == before_list:
                insert_line_number = iline
                # record line number
                all_before_line_numbers.append(insert_line_number)
                # if only single match
                if not multiple_match:
                    break

        # every adding change line number
        change_line_number = 0

        for line in all_before_line_numbers:
            # add line number for before changing
            exact_line = line + change_line_number
            self.cwp[exact_line:exact_line] = add_list
            # increase line number with len(add_list)
            change_line_number += len(add_list)

    def replace_line(self, old_line: str, new_line: str, regex_match: bool = False, multiple_match: bool = False, regex_backreference=False, replace_path=False):
        '''
        replace old single line with new single line (default: only value replace, path not replace)
        CASE: change single line without after-before
        '''
        # [0] for single line
        old_list = EditConfig._ec_text_convert(
            old_line, self.step_space, self.comment_tuple, self.sep)[0]
        new_list = EditConfig._ec_text_convert(
            new_line, self.step_space, self.comment_tuple, self.sep)[0]

        if regex_backreference:
            for iline, vline in enumerate(self.cwp):
                if (re.match(fr'{old_list[0]}', vline[0]) and
                        re.match(fr'{old_list[1]}', vline[1])):
                    self.cwp[iline][0] = re.sub(
                        fr'{old_list[0]}', fr'{new_list[0]}', self.cwp[iline][0])
                    self.cwp[iline][1] = re.sub(
                        fr'{old_list[1]}', fr'{new_list[1]}', self.cwp[iline][1])
                    if not multiple_match:
                        break

        else:
            all_replace_line = []
            for iline, vline in enumerate(self.cwp):
                # for regex
                if (regex_match and
                        re.match(fr'{old_list[0]}', vline[0]) and
                        re.match(fr'{old_list[1]}', vline[1])
                    ):
                    all_replace_line.append(iline)
                    if not multiple_match:
                        break
                # non regex
                if vline == old_list:
                    all_replace_line.append(iline)
                    if not multiple_match:
                        break
            # replace with line number
            for line_num in all_replace_line:
                if replace_path:
                    self.cwp[line_num] = new_list
                else:
                    self.cwp[line_num][1] = new_list[1]

    def replace_serial_lines(self, old_serial_lines: str, new_serial_lines: str, regex_match: bool = False, multiple_match: bool = False):
        '''
        replace serial lines
        CASE: partial replace
        '''
        delete_list = EditConfig._ec_text_convert(
            old_serial_lines, self.step_space, self.comment_tuple, self.sep)
        replace_list = EditConfig._ec_text_convert(
            new_serial_lines, self.step_space, self.comment_tuple, self.sep)

        # e.g [(start_iline,end_iline),]
        len_dl = len(delete_list)
        cont = True
        while cont:
            cont = False
            for iline, vline in enumerate(self.cwp):
                # for regex_match
                if (regex_match and re.match(fr'{delete_list[0][0]}', vline[0]) and
                        re.match(fr'{delete_list[0][1]}', vline[1])):
                    cwp_part_list = self.cwp[iline:iline+len_dl]
                    # regex match for every path and config line
                    if (all((re.match(fr'{i[0]}', j[0]) for i, j in zip(delete_list, cwp_part_list))) and
                            all((re.match(fr'{i[1]}', j[1]) for i, j in zip(delete_list, cwp_part_list)))):
                        # del self.cwp[iline:iline+len_dl]
                        cwp_delete_before_part = self.cwp[:iline]
                        cwp_delete_after_part = self.cwp[iline+len_dl:]
                        self.cwp = cwp_delete_before_part + replace_list + cwp_delete_after_part
                        cont = True
                        # if only single match not continue
                        if not multiple_match:
                            cont = False
                        break
                elif vline == delete_list[0] and self.cwp[iline:iline+len_dl] == delete_list:
                    # del self.cwp[iline:iline+len_dl]
                    cwp_delete_before_part = self.cwp[:iline]
                    cwp_delete_after_part = self.cwp[iline+len_dl:]
                    self.cwp = cwp_delete_before_part + replace_list + cwp_delete_after_part
                    cont = True
                    # if only single match not continue
                    if not multiple_match:
                        cont = False
                    break
        if regex_match:
            self.cwp_update()

    def replace_between_lines(self, start_with_line: str, end_with_line: str, new_serial_lines: str, regex_match: bool = False, multiple_match: bool = False):
        '''
        replace between <start_with_line> and <end_with_line> single line (first match only (non-greedy), start-end included)
        CASE: replace tree/path
        '''
        start_with = EditConfig._ec_text_convert(
            start_with_line, self.step_space, self.comment_tuple, self.sep)[0]
        end_with = EditConfig._ec_text_convert(
            end_with_line, self.step_space, self.comment_tuple, self.sep)[0]

        replace_list = EditConfig._ec_text_convert(
            new_serial_lines, self.step_space, self.comment_tuple, self.sep)

        # for regex_match
        if regex_match:
            cont = True
            while cont:
                cont = False
                start_line = None
                for iline, vline in enumerate(self.cwp):
                    # find start_line if start_line NOT found before
                    if (start_line is None and
                        re.match(fr'{start_with[0]}', vline[0]) and
                            re.match(fr'{start_with[1]}', vline[1])):
                        start_line = iline
                    # find end_line if start_line found before
                    if (start_line is not None and
                        re.match(fr'{end_with[0]}', vline[0]) and
                            re.match(fr'{end_with[1]}', vline[1])):
                        end_line = iline
                        # del between start and end
                        # del self.cwp[start_line:end_line+1]
                        cwp_delete_before_part = self.cwp[:start_line]
                        cwp_delete_after_part = self.cwp[end_line+1:]
                        self.cwp = cwp_delete_before_part + replace_list + cwp_delete_after_part
                        # if multiple_match <while> continue
                        if multiple_match:
                            cont = True
                        # exit from for
                        break

        # without regex
        else:
            while start_with in self.cwp:
                # first index
                fi_line = self.cwp.index(start_with)
                # end index after fi
                ei_line = self.cwp[fi_line:].index(end_with)
                # del fi to ei
                # del self.cwp[fi_line:(fi_line+ei_line+1)]
                cwp_delete_before_part = self.cwp[:fi_line]
                cwp_delete_after_part = self.cwp[fi_line+ei_line+1:]
                self.cwp = cwp_delete_before_part + replace_list + cwp_delete_after_part
                # if no multiple_match exit from <while> or check with while
                if not multiple_match:
                    break
        if regex_match:
            self.cwp_update()
