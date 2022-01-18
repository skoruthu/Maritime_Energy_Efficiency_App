from django.shortcuts import render
from django.db import connections
from django.shortcuts import redirect
from django.http import Http404
from django.db.utils import IntegrityError
from plotly.offline import plot
import plotly.graph_objects as go
import plotly.express as px

from app.utils import namedtuplefetchall, clamp
from app.forms import ImoForm

PAGE_SIZE = 20
COLUMNS = [
    'imo',
    'ship_name',
    'type',
    'technical_efficiency_number',
    'issue',
    'expiry'
]
VERIFIER_COLUMNS = [
    'verifier_number',
    'verifier_name',
    'verifier_nab',
    'verifier_address',
    'verifier_city',
    'verifier_country'
]

def index(request):
    """Shows the main page"""
    context = {'nbar': 'home'}
    return render(request, 'index.html', context)


def db(request):
    """Shows very simple DB page"""
    with connections['default'].cursor() as cursor:
        cursor.execute('INSERT INTO app_greeting ("when") VALUES (NOW());')
        cursor.execute('SELECT "when" FROM app_greeting;')
        greetings = namedtuplefetchall(cursor)

    context = {'greetings': greetings, 'nbar': 'db'}
    return render(request, 'db.html', context)


def emissions(request, page=1):
    """Shows the emissions table page"""
    msg = None
    order_by = request.GET.get('order_by', '')
    order_by = order_by if order_by in COLUMNS else 'imo'

    with connections['default'].cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM co2emission_reduced')
        count = cursor.fetchone()[0]
        num_pages = (count - 1) // PAGE_SIZE + 1
        page = clamp(page, 1, num_pages)

        offset = (page - 1) * PAGE_SIZE
        cursor.execute(f'''
            SELECT {", ".join(COLUMNS)}
            FROM co2emission_reduced
            ORDER BY {order_by}
            OFFSET %s
            LIMIT %s
        ''', [offset, PAGE_SIZE])
        rows = namedtuplefetchall(cursor)

    imo_deleted = request.GET.get('deleted', False)
    if imo_deleted:
        msg = f'✔ IMO {imo_deleted} deleted'

    context = {
        'nbar': 'emissions',
        'page': page,
        'rows': rows,
        'num_pages': num_pages,
        'msg': msg,
        'order_by': order_by
    }
    return render(request, 'emissions.html', context)


def insert_update_values(form, post, action, imo):
    """
    Inserts or updates database based on values in form and action to take,
    and returns a tuple of whether action succeded and a message.
    """
    if not form.is_valid():
        return False, 'There were errors in your form'

    # Set values to None if left blank
    cols = COLUMNS[:]
    values = [post.get(col, None) for col in cols]
    values = [val if val != '' else None for val in values]

    if action == 'update':
        # Remove imo from updated fields
        cols, values = cols[1:], values[1:]
        with connections['default'].cursor() as cursor:
            cursor.execute(f'''
                UPDATE co2emission_reduced
                SET {", ".join(f"{col} = %s" for col in cols)}
                WHERE imo = %s;
            ''', [*values, imo])
        return True, '✔ IMO updated successfully'

    # Else insert
    with connections['default'].cursor() as cursor:
        cursor.execute(f'''
            INSERT INTO co2emission_reduced ({", ".join(cols)})
            VALUES ({", ".join(["%s"] * len(cols))});
        ''', values)
    return True, '✔ IMO inserted successfully'


def emission_detail(request, imo=None):
    """Shows the form where the user can insert or update an IMO"""
    success, form, msg, initial_values = False, None, None, {}
    is_update = imo is not None

    if is_update and request.GET.get('inserted', False):
        success, msg = True, f'✔ IMO {imo} inserted'

    if request.method == 'POST':
        # Since we set imo=disabled for updating, the value is not in the POST
        # data so we need to set it manually. Otherwise if we are doing an
        # insert, it will be None but filled out in the form
        if imo:
            request.POST._mutable = True
            request.POST['imo'] = imo
        else:
            imo = request.POST['imo']

        form = ImoForm(request.POST)
        action = request.POST.get('action', None)

        if action == 'delete':
            with connections['default'].cursor() as cursor:
                cursor.execute('DELETE FROM co2emission_reduced WHERE imo = %s;', [imo])
            return redirect(f'/emissions?deleted={imo}')
        try:
            success, msg = insert_update_values(form, request.POST, action, imo)
            if success and action == 'insert':
                return redirect(f'/emissions/imo/{imo}?inserted=true')
        except IntegrityError:
            success, msg = False, 'IMO already exists'
        except Exception as e:
            success, msg = False, f'Some unhandled error occured: {e}'
    elif imo:  # GET request and imo is set
        with connections['default'].cursor() as cursor:
            cursor.execute('SELECT * FROM co2emission_reduced WHERE imo = %s', [imo])
            try:
                initial_values = namedtuplefetchall(cursor)[0]._asdict()
            except IndexError:
                raise Http404(f'IMO {imo} not found')

    # Set dates (if present) to iso format, necessary for form
    # We don't use this in class, but you will need it for your project
    for field in ['doc_issue_date', 'doc_expiry_date']:
        if initial_values.get(field, None) is not None:
            initial_values[field] = initial_values[field].isoformat()

    # Initialize form if not done already
    form = form or ImoForm(initial=initial_values)
    if is_update:
        form['imo'].disabled = True

    context = {
        'nbar': 'emissions',
        'is_update': is_update,
        'imo': imo,
        'form': form,
        'msg': msg,
        'success': success
    }
    return render(request, 'emission_detail.html', context)

def aggregation(request, page=1):
    """Shows the aggregation table page"""
    msg = None
    order_by = request.GET.get('order_by', '')
    order_by = order_by if order_by in COLUMNS else 'imo'
    
    with connections['default'].cursor() as cursor:
        cursor.execute('SELECT count(distinct(type)) FROM co2emission_reduced;')
        count = cursor.fetchone()[0]
        num_pages = (count - 1) // PAGE_SIZE + 1
        page = clamp(page, 1, num_pages)

        offset = (page - 1) * PAGE_SIZE
        cursor.execute(f'''
            SELECT type, count(imo), min(technical_efficiency_number), avg(technical_efficiency_number), max(technical_efficiency_number)
            FROM co2emission_reduced
            GROUP BY type
            ORDER BY type
            OFFSET %s
            LIMIT %s
        ''', [offset, PAGE_SIZE])
        rows = namedtuplefetchall(cursor)

    imo_deleted = request.GET.get('deleted', False)
    if imo_deleted:
        msg = f'✔ IMO {imo_deleted} deleted'

    context = {
        'nbar': 'aggregation',
        'page': page,
        'rows': rows,
        'num_pages': num_pages,
        'msg': msg,
        'order_by': order_by
    }
    return render(request, 'aggregation.html', context)

def create_checkboxes(params, checkboxes):

    for checkbox in checkboxes:
        for option in checkbox["options"]:
            if option["value"] in params.getlist(checkbox["id"], []):
                option["checked"] = True
            else:
                option["checked"] = False

    return checkboxes

def visual_view(request):
    """ 
    Displaying graph with plotly
    """
    with connections['default'].cursor() as cursor:
        query = 'SELECT type, count(imo), min(technical_efficiency_number), avg(technical_efficiency_number), max(technical_efficiency_number) FROM co2emission_reduced GROUP BY type ORDER BY type;'
        cursor.execute(query)
        records = cursor.fetchall()

        dict_df = {'type':[],'count':[], 'min': [], 'avg':[], 'max':[]}
        for rows in records:
            dict_df['type'].append(rows[0])
            dict_df['count'].append(rows[1])
            dict_df['min'].append(rows[2])
            dict_df['avg'].append(rows[3])
            dict_df['max'].append(rows[4])
    
    # Setting layout of the figure.
    bar_layout = {
        'title': 'Max, Min and Average EEDI per Ship Type',
        'xaxis_title': 'Ship Type',
        'yaxis_title': 'EEDI values',
        'height': 700,
        'width': 1000,
    }

    pie_layout = {
        'title': '# of Ships per Ship Type',
        'height': 700,
        'width': 1000,
    }

    box_layout = {
        'title': 'Distribution Overview of Max EEDI',
        'height': 700,
        'width': 1000,
    }

    box_layout1 = {
        'title': 'Distribution Overview of Min EEDI',
        'height': 700,
        'width': 1000,
    }

    box_layout2 = {
        'title': 'Distribution Overview of Average EEDI',
        'height': 700,
        'width': 1000,
    }

    # List of graph objects for figure.
    bar_graphs = go.Figure(data =[go.Bar(x=dict_df['type'], y=dict_df['max'], name='Max EEDI'), go.Bar(x=dict_df['type'], y=dict_df['min'], name='Min EEDI'), go.Bar(x=dict_df['type'], y=dict_df['avg'], name='Average EEDI')], layout=bar_layout)
    bar_graphs.update_layout(barmode='group')

    pie_graphs = go.Figure(data=[go.Pie(labels=dict_df['type'], values=dict_df['count'])], layout=pie_layout)

    box_graphs = go.Figure(data=[go.Box(x=dict_df['max'], name='Max EEDI', marker_color = 'indianred')], layout = box_layout)
    box_graphs1 = go.Figure(data=[go.Box(x=dict_df['min'], name='Min EEDI', marker_color = 'royalblue')], layout = box_layout1)
    box_graphs2 = go.Figure(data=[go.Box(x=dict_df['avg'], name='Average EEDI', marker_color = 'lightseagreen')], layout = box_layout2)

    # Getting HTML needed to render the plot.
    bar_div = plot({'data': bar_graphs, 'layout': bar_layout}, output_type='div')
    pie_div = plot({'data': pie_graphs, 'layout': pie_layout}, output_type='div')
    box_div = plot({'data': box_graphs, 'layout': box_layout}, output_type='div')
    box_div1 = plot({'data': box_graphs1, 'layout': box_layout1}, output_type='div')
    box_div2 = plot({'data': box_graphs2, 'layout': box_layout2}, output_type='div')

    checkbox = [
        {
            'id': 'year',
            'label': 'Year',
            'options': [
                {
                    'value': '2020',
                    'label': '2020',
                    'checked': True
                },
                {
                    'value': '2021',
                    'label': '2021',
                    'checked': True
                }
            ]
        },
        {
            'id': 'century',
            'label': 'Century',
            'options': [
                {
                    'value': '19',
                    'label': '19',
                    'checked': True
                },
                {
                    'value': '20',
                    'label': '20',
                    'checked': False
                },
                {
                    'value': '20',
                    'label': '20',
                    'checked': True
                }
            ]
        },
    ]

    # Setting context
    context={
        'graphs': [
            bar_div,
            pie_div,
            box_div,
            box_div1,
            box_div2
        ],
        'checkboxes': create_checkboxes(request.GET, checkbox)
    }

    return render(request, 'visual.html', context)

def extended_view(request):
    """ 
    Displaying graph with plotly
    """
    # get params request.
    request_dict = request.GET
    print(request_dict)
    if request_dict != {}:
        y_axis = request_dict['y_axis']
        query = "SELECT s.ship_type, s.engine_type, ROUND(AVG({})::NUMERIC,2) as metric, ROUND(AVG(f.fuel_consumption)::NUMERIC,2) as fuelconsumption,LN(COUNT(*)) as scaled_count, (CASE  WHEN s.ship_type ISNULL AND s.engine_type ISNULL THEN 'Grand Total' WHEN s.engine_type ISNULL THEN 'Subtotal'||' '||s.ship_type ELSE s.ship_type|| ' ' || s.engine_type END) as label FROM fact_table f, ship_dimension s WHERE f.ship_key = s.ship_key GROUP BY ROLLUP(s.ship_type, s.engine_type) ORDER BY s.ship_type DESC, s.engine_type DESC".format(y_axis)
    else:
        size = 'Ln(count) of Ships'
        y_axis = 'f.eedi'
        x_axis = 'Average Fuel Consumption'
        query = "SELECT s.ship_type, s.engine_type, ROUND(AVG(f.eedi)::NUMERIC,2) as metric, ROUND(AVG(f.fuel_consumption)::NUMERIC,2) as fuelconsumption,LN(COUNT(*)) as scaled_count, (CASE  WHEN s.ship_type ISNULL AND s.engine_type ISNULL THEN 'Grand Total' WHEN s.engine_type ISNULL THEN 'Subtotal'||' '||s.ship_type ELSE s.ship_type|| ' ' || s.engine_type END) as label FROM fact_table f, ship_dimension s WHERE f.ship_key = s.ship_key GROUP BY ROLLUP(s.ship_type, s.engine_type) ORDER BY s.ship_type DESC, s.engine_type DESC"

    with connections['default'].cursor() as cursor:
        cursor.execute(query)
        records = cursor.fetchall()

        dict_df = {'size':[],'y_axis':[], 'x_axis': [], 'label': []}
        for rows in records:
            dict_df['y_axis'].append(rows[2])
            dict_df['x_axis'].append(rows[3])
            dict_df['size'].append(rows[4])
            dict_df['label'].append(rows[5])
    
    # Setting layout of the figure.
    bubble_layout = {
        'height': 700,
        'width': 1000,
    }

    y_axis_title = {'f.eedi': 'EEDI', 's.tonnage' : "Ship Tonnage Capacity", 's.width': 'Ship Width', 's.length': 'Ship Length', 's.speed': 'Ship Speed', 's.engine_type': 'Ship Engine Type', 'f.sea_time': 'Sea Time', 'f.co2_distance': 'CO2 Distance', 'f.co2_transport':'CO2 Transport'}

    # List of graph objects for figure.
    graph_title = 'Average fuel consumption vs {} per Ship Type and Ship Engine (with Subtotal for each Type and Engine)'.format(y_axis_title[y_axis])
    bubble_div = px.scatter(x=dict_df['x_axis'], y=dict_df['y_axis'], size=dict_df['size'], color=dict_df['label'], labels={'x':'Average fuel consumption', 'y':y_axis_title[y_axis], 'color':'Value of Bubbles'}, title=graph_title, log_x=True, size_max=60)

    # Getting HTML needed to render the plot.
    bubble_graph = plot({'data': bubble_div, 'layout': bubble_layout}, output_type = 'div')

    # Setting context
    context={
        'graphs': [
            bubble_graph
        ],
        'selected_metrics': 'Current Selected Performance Metrics & Ship Features:',
        'chosen_metrics': y_axis_title[y_axis],
        'title': 'Fuel Consumption vs Performance Metrics/Ship Features of each Ship Type and Engine',
        'description': 'We compared fuel consumption of every ship type and engine with their features and different maritime performance metrics. This is so that we can understand if there are any correlations between different performance metrics or ship features with fuel consumption. Size of the bubbles are determined by natural logarithm of ship count, ensuring the relative importance by ship type is captured.',
        'interaction': 'To select different performance metrics or ship features, use the dropdown below. You can focus on the information of a particular ship type by hovering over the bubbles displayed.',
        'dropdowns': [
            {
                'id': 'y_axis',
                'label': 'Performance Metrics & Ship Features',
                'options': [
                    {
                        'value': 'f.eedi',
                        'label': 'Select here'
                    },
                    {
                        'value': 'f.eedi',
                        'label': 'EEDI'
                    },
                    {
                        'value': 's.tonnage',
                        'label': 'Tonnage'
                    },
                    {
                        'value': 's.width',
                        'label': 'Width'
                    },
                    {
                        'value': 's.length',
                        'label': 'Length'
                    },
                    {
                        'value': 's.engine_type',
                        'label': 'Engine Type'
                    },
                    {
                        'value': 's.speed',
                        'label': 'Speed'
                    },
                    {
                        'value': 'f.sea_time',
                        'label': 'Sea Time'
                    },
                    {
                        'value': 'f.co2_distance',
                        'label': 'CO2 Distance'
                    },
                    {
                        'value': 'f.co2_transport',
                        'label': 'CO2 Transport'
                    }
                ]
            }
        ]
    }

    return render(request, 'visual.html', context)

def extended_view_graph2(request):
    """ 
    Displaying graph with plotly
    """
    
    # get params request.
    request_dict = request.GET
    size = 'Count of Ships'
    y_axis = 'Average EEDI'
    x_axis = 'Average Fuel Consumption'
    query = 'SELECT v.verifier_name, d.month_actual, ROUND(AVG(f.EEDI)::NUMERIC,2) as avg_eedi, RANK() OVER(PARTITION BY d.month_actual ORDER BY ROUND(AVG(f.EEDI)::NUMERIC,2) ASC) rank FROM fact_table f, verifiers v, d_date d WHERE f.issue_date_key = d.date_dim_id AND f.verifier_key = v.verifier_key AND f.verifier_key IN (SELECT DISTINCT verifier_key FROM verifiers) GROUP BY v.verifier_name, d.month_actual;'
    
    with connections['default'].cursor() as cursor:
        cursor.execute(query)
        records = cursor.fetchall()

        dict_df = {'color':[],'y_axis':[], 'x_axis': []}
        for rows in records:
            dict_df['color'].append(rows[0])
            dict_df['x_axis'].append(rows[1])
            dict_df['y_axis'].append(rows[3])

    # List of graph objects for figure.
    graph_title = 'Longitudinal Tracking of Average EEDI for Accredited Vessels by Verifier'
    line_div = px.line(x=dict_df['x_axis'], y=dict_df['y_axis'], color=dict_df['color'], labels={'x':'Issue Month', 'y':'Rank against other verifiers', 'color': 'Verifiers Name'}, title=graph_title)

    # Getting HTML needed to render the plot.
    line_graph = plot({'data': line_div}, output_type = 'div')

    # Setting context
    context={
        'graphs': [
            line_graph
        ],
        'selected_metrics': '',
        'chosen_metrics': '',
        'title': 'Ranking Verifiers based on EEDI',
        'description': 'We ranked verifiers based on the average EEDI of all their certified ships, tracked across post issuance months.',
        'interaction': 'Remove any verifier from the graph by clicking on their names. Reselect to add their rank back to the graph. Verifiers that are not selected will have a grey font instead of black.',
    }

    return render(request, 'visual.html', context)

def extended_view_graph3(request):
    # get params request.
    request_dict = request.GET
    print(request_dict)
    if request_dict != {}:
        y_axis = request_dict['y_axis']
        query = 'SELECT s.year_built, ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY f.{} ASC)::NUMERIC,2) AS percentile_25, ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY f.{} ASC)::NUMERIC,2) AS percentile_75 FROM fact_table f, ship_dimension s WHERE f.ship_key = s.ship_key GROUP BY s.year_built'.format(y_axis, y_axis)
    else:
        size = 'Count of Ships'
        y_axis = 'Average EEDI'
        x_axis = 'Average Fuel Consumption'
        query = 'SELECT s.year_built, ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY f.eedi ASC)::NUMERIC,2) AS percentile_25, ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY f.eedi ASC)::NUMERIC,2) AS percentile_75 FROM fact_table f, ship_dimension s WHERE f.ship_key = s.ship_key GROUP BY s.year_built;'
    
    with connections['default'].cursor() as cursor:
        cursor.execute(query)
        records = cursor.fetchall()

        dict_df = {'x_axis':[],'y_axis':[], 'y_axis1': []}
        for rows in records:
            dict_df['x_axis'].append(rows[0])
            dict_df['y_axis'].append(rows[1])
            dict_df['y_axis1'].append(rows[2])

    if y_axis == 'fuel_consumption':
        y_axis_title = 'Fuel Consumption'
    elif y_axis == 'co2_distance':
        y_axis_title = 'CO2 Distance'
    elif y_axis == 'co2_transport':
        y_axis_title = 'CO2 Transport'
    else:
        y_axis_title = 'EEDI'

    bar_layout = {
        'title': '25th and 75th Percentiles of {} for all ship based on year built'.format(y_axis_title),
        'xaxis_title': 'Year Built',
        'yaxis_title': y_axis_title,
        'height': 700,
        'width': 1000,
    }

    # List of graph objects for figure.
    graph_title = 'Percentile Bar Rank'
    bar_graphs = go.Figure(data =[go.Bar(x=dict_df['x_axis'], y=dict_df['y_axis'], name='25th Percentile'), go.Bar(x=dict_df['x_axis'], y=dict_df['y_axis1'], name='75th Percentile')], layout=bar_layout)
    bar_graphs.update_layout(barmode='group')

    # Getting HTML needed to render the plot.
    bar_div = plot({'data': bar_graphs, 'layout': bar_layout}, output_type='div')

    # Setting context
    context={
        'graphs': [
            bar_div
        ],
        'selected_metrics': 'Current Selected Efficiency Metrics:',
        'chosen_metrics': y_axis_title,
        'dropdowns': [
            {
                'id': 'y_axis',
                'label': 'Efficiency Metrics',
                'options': [
                    {
                        'value': 'eedi',
                        'label': 'Select here'
                    },
                    {
                        'value': 'eedi',
                        'label': 'EEDI'
                    },
                    {
                        'value': 'co2_distance',
                        'label': 'CO2 Distance'
                    },
                    {
                        'value': 'co2_transport',
                        'label': 'CO2 Transport'
                    },
                    {
                        'value': 'fuel_consumption',
                        'label': 'Fuel Consumption'
                    }
                ]
            }
        ],
        'title': 'Measuring Efficiency of Ships Built in Different Years',
        'description': 'We computed the 25th and 75th percentile values of various reported efficiency metrics, segmented across year of vessel build. Said metrics include: EEDI, C02 transport, CO2 distance and Fuel consumption.',
        'interaction': 'To select different metrics, use the dropdown below. You can view both percentiles or focus on one percentile by hovering over the bars displayed.'
    }

    return render(request, 'visual.html', context)