from django import template

register = template.Library()

def split_text(value, max_length=40):
    result = []
    line = ''
    char_count = 0

    for char in value:
        line += char
        char_count += 1
        if char_count == max_length:
            result.append(line)
            line = ''
            char_count = 0

    if line:
        result.append(line)

    return "\n".join(result)

register.filter('split_text', split_text)


def reverse_list(value):
    return reversed(value)

register.filter('reverse', reverse_list)
