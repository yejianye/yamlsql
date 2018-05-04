from tabulate import tabulate

def describe_table(data):
    if data['type'] == 'table':
        text = tabulate([[r['field'], r['type']] for r in data['fields']],
                        headers=['field', 'type'],
                        talbefmt='orgtbl')
        return {
            'text': text
            }
    elif data['type'] == 'view':
        return {
            'text': data['definition']
            }
