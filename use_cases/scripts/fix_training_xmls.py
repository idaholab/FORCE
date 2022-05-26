from argparse import ArgumentError
import os
import shutil
import sys


def comment_line_xml(line):
    open_bracket_ind = line.find('<')
    new_line = line[:open_bracket_ind] + '<!--' + line[open_bracket_ind:-1] + '-->\n'
    return new_line


def comment_bad_lines(lines, node_names):
    edited_lines = []

    for i, l in enumerate(lines):
        for name in node_names:
            if name in l:
                lines[i] = comment_line_xml(l)
                print('\tCommenting out line', i)
                edited_lines.append(i)
                break

    return lines, edited_lines


def fix_training_xmls(dirpath):
    """
    This comments out the first line that the node is found at.
    TODO: This should be fixed to also find the line with the closing node and comment out everything in between.
    """
    bad_node_names = ['<clusterEvalMode>']
    
    for root, dirs, files in os.walk(dirpath):
        for fname in files:
            if fname.endswith('.xml'):
                read_fpath = os.path.join(root, fname)
                print('Parsing file', read_fpath)
                with open(read_fpath, 'r') as fr:
                    lines = fr.readlines()
                new_lines, edited_line_inds = comment_bad_lines(lines, bad_node_names)
                new_lines, was_verb_changed = change_xml_verbosity(new_lines)
                if edited_line_inds or was_verb_changed:
                    print('File', read_fpath, 'was edited. Writing changes.')
                    for i in edited_line_inds:
                        print(new_lines[i])
                    print('Verbosity was {}changed'.format('' if was_verb_changed else 'not '))
                    write_fpath = os.path.join(root, fname)
                    with open(write_fpath, 'w') as fw:
                        fw.writelines(new_lines)


def change_xml_verbosity(lines):
    is_changed = False
    
    for i, l in enumerate(lines):
        verbosity_setting = None
        if 'verbosity="debug"' in l:
            verbosity_setting = 'verbosity="debug"'
        elif "verbosity='all'" in l:
            verbosity_setting = "verbosity='debug'"
        
        if verbosity_setting is not None:
            lines[i] = l.replace(verbosity_setting, 'verbosity="all"')
            is_changed = True
            break

    return lines, is_changed


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 2:
        raise ArgumentError
    for dpath in args[1:]:
        fix_training_xmls(dpath)
