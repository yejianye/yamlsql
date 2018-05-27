from tabulate import tabulate


def describe_table(data):
    text = tabulate([[r['field'], r['type']] for r in data['fields']],
                    headers=['field', 'type'],
                    tablefmt='orgtbl')
    return {
        'text': text
        }


DESCRIBE_FIELD_TMPL = """
[Stats for {}]
{}

[Common Values]
{}
"""
def describe_field(data):
    keys = ['distinct_count', 'min', 'max', 'avg']
    display_names = [k.capitalize().replace('_', ' ') for k in keys]
    stats = tabulate([(name, data[key]) for name, key in
                      zip(display_names, keys)
                      if key in data],
                     tablefmt='plain')
    most_common = tabulate([(x['value'], x['count']) for x in data['most_common']],
                           headers=['Value', 'Count'],
                           tablefmt='simple')
    return {
        'text': DESCRIBE_FIELD_TMPL.format(
            data['field_name'],
            stats,
            most_common).strip()
        }

def run_sql(data):
    result = tabulate(data['rows'], headers=data['columns'], tablefmt='simple')
    return {
        'text': result
        }
