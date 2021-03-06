import os
import sys
import pandas as pd
import numpy as np
import plotly.plotly as py
import dash_daq as daq
from textwrap import dedent as d
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import dash_table


try:
    import dash
except ModuleNotFoundError:
    print ('You must install dash: pip install dash')
    sys.exit
    
try:
    import dash_core_components as dcc
except ModuleNotFoundError:
    print ('You must install dash-core-components: pip install dash-core-components')
    sys.exit
    
try:
    import dash_html_components as html  
except ModuleNotFoundError:
    print ('You must install dash-html-components: pip install dash-html-components')
    sys.exit
    

def getBorderColors(coursePortrait, selected_dropdown_value):
    colors=[]
    for columnName in coursePortrait.columns:
        if columnName.find('рекомендуемый объем выборки для'+selected_dropdown_value)==-1:
            colors.append('white')
        else:
            colors.append('black')
    return colors


def get_color(courseName):
    isSpecial=courseName.lower().find('спец.') #position of the substring or -1
    isSPBU=courseName.lower().find('спбгу')
    if isSpecial==-1:
        color='rgb(0,182,255)' #ordinary session is blue
    elif isSPBU!=-1:
        color='rgb(255,15,0)' #special spbu session is red 
    else:
        color='rgb(254,204,2)' #special session of another universities is orange
    return color

def get_courses_names_and_colors(selected_radio_value,df):
    courses_colors=[]
    courses_names=[]
    
    if selected_radio_value=='all':
        courses_names=df.курс.unique()
        for courseName in df.курс:
            courses_colors.append(get_color(courseName))            
            
    elif selected_radio_value=='special':
        for courseName in df.курс:   
            isSpecial=courseName.lower().find('спец.') #position of the substring or -1
            if isSpecial!=-1:
                courses_colors.append(get_color(courseName))
                courses_names.append(courseName)

    elif selected_radio_value=='with_spec_spbu':  
        for courseName in df.курс.unique():            
            isSPBU=courseName.lower().find('спбгу')
            if isSPBU!=-1:
                course=courseName.lower().split(' (спец.')[0]
                for courseNameInAll in df.курс:
                    isCurrentCourse=courseNameInAll.lower().find(course)
                    if isCurrentCourse!=-1:
                        courses_colors.append(get_color(courseNameInAll))
                        courses_names.append(courseNameInAll)
        
                
    elif selected_radio_value=='spec_spbu':
        for courseName in df.курс:
            isSPBU=courseName.lower().find('спбгу')
            if isSPBU!=-1:
                courses_names.append(courseName)
                courses_colors.append('rgb(255,15,0)')                
                
    courses_names=np.unique(courses_names)        
    return courses_names,courses_colors

def assessmentsGraphs(df, surveysCounter,coursePortrait,avgErr,textResults,textFields):
    os.chdir('..')
    df=df.sort_values(by='курс')
    
    columns=textFields.copy()
    columns.append('курс')
    allTextsData=df[columns]
    
    assessmentOptions=[]
    for column in df.columns:     
        if column.split(' ')[0]=='оценка':
            assessmentOptions.append({'label': column, 'value': column})       
    
    sessionColorsInPortrait=[]    
    for courseName in coursePortrait.курс:
        sessionColorsInPortrait=get_color(courseName)
            
    sessionColorsInDF=[]
    for courseName in df.курс:
        isSpecial=courseName.lower().find('спец.') #position of the substring or -1
        isSPBU=courseName.lower().find('спбгу')
        if isSpecial==-1:
            sessionColorsInDF.append('rgb(0,182,255)') #ordinary session is blue
        elif isSPBU!=-1:
            sessionColorsInDF.append('rgb(255,15,0)') #special spbu session is red
        else:
            sessionColorsInDF.append('rgb(254,204,2)') #special session of another universities is orange
            
    app = dash.Dash()   
    
    app.layout = html.Div(children=[
        html.Div(children='Количество обработанных анкет: '+str(surveysCounter)),
        
        dcc.RadioItems(
            id='courses_radio',
            options=[
                {'label': 'Показать информацию по всем курсам', 'value': 'all'},
                {'label': 'Показать только спец.сессии', 'value': 'special'},
                {'label': 'Показать все курсы, у которых есть спец.сессия СПбГУ', 'value': 'with_spec_spbu'},
                {'label': 'Показать только спец.сессии СПбГУ', 'value': 'spec_spbu'}           
            ],
            labelStyle={'display': 'block'},
            value='all'
        ),
        

        dcc.Graph(id='количество отзывов'),
        
        html.Div([
            html.H2('Информация по текстовым полям', className='row',style={'padding-top': '20px'}),
            html.P('Нажмите на столбец на графике выше, чтобы получить информацию по текстовым полям.', 
                   className='row', 
                   style={'padding-left': '30px','fontSize': 20}),
            html.Pre(id='click-data'),
        ], className='three columns'),
        
        html.H2('Выберите графики:', className='row',
                            style={'padding-top': '20px'}),
        dcc.Dropdown(
            id='my-dropdown',
            options=assessmentOptions
        ),

       
        
        dcc.Graph(id='avggraph'),
        
        html.Div([html.P('На данном графике изображены средние оценки для каждого курса. Черным обведены нерелевантные данные - объем выборки является недостаточным для рассматриваемой оценки. Красным цветом выделены специальные сессии СПбГУ, желтым - другие специальные сессии, синим - все остальные сессии.', className='row', style={'padding-left': '30px','fontSize': 20})]),
         
        

        dcc.Graph(id='boxgraph'),
       
        html.Div([html.P('На данном графике отмечены все основные статистики данных. Цветовая гамма точек выбрана по тому же принципу, что и на графике выше.', className='row',style={'padding-left': '30px','fontSize': 20})]),
        html.Div([html.P('Диаграмма размаха ("ящик с усами"), содержит следующую информацию:', className='row',style={'padding-left': '30px','fontSize': 20})]),
        html.Div([html.Ul([
            html.Li("max - максимальное значение, встречаемое в данных."),
            html.Li("q1 - первый квартиль. Значение, которое данные не превышают с вероятностью 25%."),
            html.Li("median - медиана выборки. Эта статистика показывает, сколько средний человек принесет в данные. Медиана является более устойчивой к выбросам, чем среднее значение."),
            html.Li("q3 - третий квартиль. Значение, которое данные не превышают с вероятностью 75%."),
            html.Li("min - минимальное значение, встречаемое в данных."),
            html.Li("lower fence - нижняя граница \"уса\". Нижняя граница статистически значимой выборки. Всё что ниже - выбросы, которые не имеют значения."),
            html.Li("upper fence - верхняя граница \"уса\". Верхняя граница статистически значимой выборки. Всё что выше - выбросы, которые не имеют значения."),
            html.Li("точки-выбросы - точки за пределами \"ящика с усами\". Эти точки являются аномалиями по отношению к остальной выборке."),
            html.Li("линии-усы показывают степень разброса данных.")
        ],className='row',style={'padding-left': '30px','fontSize': 20})]),
        html.Div([html.P('', className='row',style={'padding-left': '30px','fontSize': 20})]),
        
        
        dcc.Graph(id='allgraph'),
       
        html.Div([html.P('На данном графике отмечены все оценки, которые пользователи указывали для конкретного курса. Цветовая гамма точек выбрана по тому же принципу, что и на графике выше. Чем больше оценок - тем ярче отметка', className='row',style={'padding-left': '30px','fontSize': 20})])
        
    ], style={'width': '1000','heigth':'1000'} )
    
    
    @app.callback(Output('количество отзывов', 'figure'), [Input('courses_radio', 'value')])
    def update_maingraph(selected_radio_value):
        courses_names,courses_colors=get_courses_names_and_colors(selected_radio_value,coursePortrait) 
        res={
            'data': [
                {'x':coursePortrait.loc[coursePortrait['курс'].isin(courses_names)]['курс'], 
                 'y':coursePortrait.loc[coursePortrait['курс'].isin(courses_names)]['количество отзывов на курс'], 
                 'marker': {
                     'color': courses_colors
                 },    
                 'type':'bar',
                 'name':[courses_names],                 
                },
            ],
            'layout': {'title': 'График количества отзывов на каждый курс'}
        }

        return res
    
    @app.callback(Output('click-data', 'children'),[Input('количество отзывов', 'clickData')])
    def display_click_data(clickData):
        if clickData:
            course=clickData['points'][0]['x']
            resultThemesData=textResults.loc[textResults['курс'] == course]
            textsData=allTextsData.loc[allTextsData['курс']==course]
            
            children=[]
            if textsData.shape[0]>3:
                children.append(
                    html.P('Тематика отзывов по курсу: '+course, 
                           className='row', 
                           style={'padding-left': '30px','font-family':'Times New Roman','fontSize': 20})
                )
                
                columns=resultThemesData.columns.values.tolist()
                columns.remove('курс')
                
                children.append(
                    dash_table.DataTable(
                        id='table',
                        columns=[{"name": i, "id": i} for i in columns],
                        style_cell={'minWidth': '150px','textAlign': 'left'},
                        data=resultThemesData.to_dict("rows"),
                        n_fixed_rows=1,
                        style_table={
                            #'maxWidth':'1000',
                            #'overflowX': 'scroll',
                            'maxHeight': '300',
                            'overflowY': 'scroll'
                        },
                    ) 
                )
                
            if  textsData.shape[0]>0:    
                for textField in textFields:
                    
                    currentTextData=pd.DataFrame(textsData[textField]).dropna()                   
                    
                    children.append(
                        html.P(textField[0].upper()+textField[1:]+': \n Количество отзывов:'+str(currentTextData.shape[0]), 
                               className='row', 
                               style={'padding-left': '30px','font-family':'Times New Roman', 'fontSize': 20})
                    ) 
                    
                    children.append(
                        dash_table.DataTable(
                            id=textField,
                            columns=[{"name": i, "id": i} for i in currentTextData.columns],
                            style_cell={'minWidth': '150px','textAlign': 'left'},
                            data=currentTextData.to_dict("rows"),
                            n_fixed_rows=1,
                            style_table={
                                'maxHeight': '300',
                                'overflowY': 'scroll'
                            },
                        )
                    )
            else:                    
                children.append(
                        html.P('По данному курсу отзывов нет', 
                               className='row', 
                               style={'padding-left': '30px','font-family':'Times New Roman', 'fontSize': 20})
                )
                
            return html.Div(children=children)

    
    @app.callback(Output('avggraph', 'figure'), [Input('my-dropdown', 'value'),
                                                 Input('courses_radio', 'value')])
    def update_avggraph(selected_dropdown_value,selected_radio_value):
        if not (selected_dropdown_value is None):
            courses_names,courses_colors=get_courses_names_and_colors(selected_radio_value,coursePortrait)
            
            assessmentName=selected_dropdown_value[len('оценка'):]
            lineColors=coursePortrait.loc[coursePortrait['курс'].isin(courses_names)][
                'рекомендуемый объем выборки для средней оценки'+assessmentName+' при отклонении '+str(avgErr)
            ]

            graphName='Средняя '+selected_dropdown_value          
            res={
                'data': [
                    {'x': coursePortrait.loc[coursePortrait['курс'].isin(courses_names)]['курс'],
                     'y': coursePortrait.loc[coursePortrait['курс'].isin(courses_names)]['средняя '+selected_dropdown_value],
                     'marker': {
                         'color': courses_colors, 
                         'line': {'width': 1, 'color': lineColors}
                     },                     
                     'type': 'bar', 
                     'name': graphName
                    }],
                'layout': {'title': graphName}
            }
        else:
            res={}
        return res
    
    @app.callback(Output('boxgraph', 'figure'), [Input('my-dropdown', 'value'),
                                                 Input('courses_radio', 'value')])
    def update_boxgraph(selected_dropdown_value,selected_radio_value):
        if not (selected_dropdown_value is None):
            courses_names,courses_colors=get_courses_names_and_colors(selected_radio_value,coursePortrait)
            
            assessmentName=selected_dropdown_value[selected_dropdown_value.find('оценка')+len('оценка'):]            
            graphName='Диаграмма размаха оценки'+assessmentName            
            counter=0
            data=[]
           
            for course in courses_names:
                yAxis=df.loc[df['курс'] == course]['оценка'+assessmentName]
                size=yAxis.shape[0]
                fillColor=courses_colors[counter]

                data.append(
                    go.Box( 
                        name=course,
                        y=yAxis,
                        marker={
                            'color':fillColor
                        }
                    ) 
                )
                counter=counter+1

            res={
                'data': data,
                'layout': {'title': graphName, 'showlegend':False}
            }
            
        else:
            res={}
        return res
    
    
    @app.callback(Output('allgraph', 'figure'), [Input('my-dropdown', 'value'),
                                                 Input('courses_radio', 'value')])
    def update_allgraph(selected_dropdown_value,selected_radio_value):
        if not (selected_dropdown_value is None):
            courses_names,courses_colors=get_courses_names_and_colors(selected_radio_value,df)
            
            assessmentName=selected_dropdown_value[selected_dropdown_value.find('оценка'):]
            graphName=assessmentName[0].upper()+assessmentName[1:]          
            
            res={
                'data': [
                    go.Scatter(
                        x=df.loc[df['курс'].isin(courses_names)]['курс'],
                        y=df.loc[df['курс'].isin(courses_names)][assessmentName],                        
                        mode='markers',
                        opacity=1,
                        marker={
                            'opacity':0.1,
                            'color': courses_colors,
                            'size': 8                            
                        },
                    ) 
                ],
                'layout': {'title': graphName}
            }
        else:
            res={}
        return res
                
                 

    app.run_server(debug=True)   