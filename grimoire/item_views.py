''' views for the item type pages '''
from flask import render_template
import logging

from grimoire import app, graph, entities
import grimoire.helpers as helpers

@app.route('/<label>/<uid>')
def item(label, uid):
    ''' generic page for an item '''
    label = helpers.sanitize(label)
    if not graph.validate_label(label):
        logging.error('Invalid label %s', label)
        return render_template('label-404.html', labels=graph.get_labels())

    uid = helpers.sanitize(uid)
    logging.info('loading %s: %s', label, uid)
    data = graph.get_node(uid)
    if not data['nodes']:
        logging.error('Invalid uid %s', uid)
        items = graph.get_all(label)
        return render_template('item-404.html', items=items['nodes'],
                               search=graph.search(uid)['nodes'], label=label)

    node = data['nodes'][0]
    rels = data['relationships']

    rel_exclusions = []
    template = 'item.html'

    if label == 'fairy':
        # removes duplication of two-way sister relationships
        rels = [r for r in rels if r['type'] != 'is_a_sister_of' or r['end']['id'] != node['id']]

    if label == 'grimoire':
        template = 'grimoire.html'
        rel_exclusions = ['lists', 'has', 'includes']
        data = grimoire_item(data, node, rels)

    elif label == 'art':
        template = 'topic.html'
        data['entities'] = {}
        rel_exclusions = ['teaches', 'skilled_in']
        for entity in entities:
            data['entities'][entity] = helpers.extract_rel_list(rels, entity, 'start')
    elif label in entities:
        template = 'entity.html'
        data = entity_item(data, node, rels)
        rel_exclusions = ['lists', 'teaches', 'skilled_in', 'serves']
    elif label == 'language':
        template = 'language.html'
        rel_exclusions = ['was_written_in']
        data['grimoires'] = helpers.extract_rel_list(rels, 'grimoire', 'start')
    elif label == 'edition':
        template = 'edition.html'
        rel_exclusions = ['published', 'edited', 'has']
        node['properties'] = {k:v for k, v in node['properties'].items() if
                              not k == 'editor'}
        data['publisher'] = helpers.extract_rel_list(rels, 'publisher', 'start')
        data['editors'] = helpers.extract_rel_list(rels, 'editor', 'start')
        data['grimoire'] = helpers.extract_rel_list(rels, 'grimoire', 'start')[0]

    data['relationships'] = [r for r in rels if not r['type'] in rel_exclusions]
    data['id'] = node['id']
    data['properties'] = {k:v for k, v in node['properties'].items() if
                          not k in ['year', 'decade', 'century']}
    data['has_details'] = len([k for k in data['properties'].keys()
                               if not k in ['uid', 'content', 'identifier']]) > 0

    sidebar = []
    related = graph.related(uid, label)
    # similar items of the same type
    if related['nodes']:
        sidebar = [{'title': 'Similar %s' % helpers.pluralize(helpers.capitalize_filter(label)),
                    'data': related['nodes']}]

    sidebar += get_others(data['relationships'], node)

    title = '%s (%s)' % (node['properties']['identifier'], helpers.capitalize_filter(label))

    return render_template(template, data=data, title=title, label=label, sidebar=sidebar)


def grimoire_item(data, node, rels):
    ''' format data for grimoires '''
    data['date'] = helpers.grimoire_date(node['properties'])
    data['editions'] = helpers.extract_rel_list(rels, 'edition', 'end')
    data['spells'] = helpers.extract_rel_list(rels, 'spell', 'end')
    data['entities'] = {}
    for entity in entities:
        data['entities'][entity] = helpers.extract_rel_list_by_type(rels, 'lists', entity, 'end')

    return data


def entity_item(data, node, rels):
    ''' format data for entities '''
    data['grimoires'] = helpers.extract_rel_list(rels, 'grimoire', 'start')
    data['skills'] = helpers.extract_rel_list(rels, 'art', 'end')
    data['serves'] = helpers.extract_rel_list_by_type(rels, 'serves', 'demon', 'end')
    data['serves'] = [s for s in data['serves'] if
                      not s['properties']['uid'] == node['properties']['uid']]
    data['servants'] = helpers.extract_rel_list_by_type(rels, 'serves', 'demon', 'start')
    data['servants'] = [s for s in data['servants'] if
                        not s['properties']['uid'] == node['properties']['uid']]
    return data


def get_others(rels, node):
    '''
    other items of the node's type related to something it is related to.
    For example: "Other editions by the editor Joseph H. Peterson"
    '''
    label = node['label']
    others = []
    for rel in rels:
        start = rel['start']
        end = rel['end']

        # must be different types of data, and not entities in a grimoire
        if start['label'] != end['label'] and \
                (end['label'] != 'demon' and start['label'] != 'grimoire'):
            # other = "editions"
            other = start if start['label'] != label else end
            other_items = graph.others_of_type(label,
                                               other['properties']['uid'],
                                               node['properties']['uid'])
            if other_items['nodes']:
                others.append({
                    'title': 'Other %s related to the %s %s' %
                             (helpers.pluralize(label), helpers.format_filter(other['label']),
                              other['properties']['identifier']),
                    'data': other_items['nodes']
                })
    return others

