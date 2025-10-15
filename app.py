import streamlit as st
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Proyectos Eólicos en Colombia",
    page_icon="🌬️",
    layout="wide"
)

# Título principal
st.title("🌬️ Análisis de Proyectos Eólicos en Colombia")
st.markdown("---")

# Función para cargar datos
@st.cache_data
def cargar_datos():
    try:
        # Cargar el shapefile
        shp_path = "datos\SHP_MGN2018_INTGRD_DEPTO\MGN_ANM_DPTOS.shp"
        st.info(f"Intentando cargar shapefile desde: {shp_path}")
        gdf = gpd.read_file(shp_path)
        st.success(f"✅ Shapefile cargado correctamente. Registros: {len(gdf)}")
        
        # Cargar el archivo Excel
        excel_path = "datos\proyectos\proyecto_colombia.xlsx"
        st.info(f"Intentando cargar Excel desde: {excel_path}")
        df_excel = pd.read_excel(excel_path)
        st.success(f"✅ Excel cargado correctamente. Registros: {len(df_excel)}")
        
        return gdf, df_excel
    except Exception as e:
        st.error(f"❌ Error al cargar los datos: {str(e)}")
        st.error(f"Tipo de error: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc())
        return None, None

# Cargar los datos
gdf, df_excel = cargar_datos()

if gdf is not None and df_excel is not None:
    
    # Procesar datos: contar proyectos por departamento
    proyectos_por_depto = df_excel['Departamento'].value_counts().reset_index()
    proyectos_por_depto.columns = ['Departamento', 'Cantidad_Proyectos']
    
    # Normalizar nombres de departamentos para hacer el merge
    # Convertir a mayúsculas y quitar espacios extras
    proyectos_por_depto['Departamento'] = proyectos_por_depto['Departamento'].str.upper().str.strip()
    gdf['DPTO_CNMBR'] = gdf['DPTO_CNMBR'].str.upper().str.strip()
    
    # Unir los datos del shapefile con los proyectos contados
    gdf_merged = gdf.merge(
        proyectos_por_depto, 
        left_on='DPTO_CNMBR', 
        right_on='Departamento', 
        how='left'
    )
    
    # Rellenar NaN con 0 (departamentos sin proyectos)
    gdf_merged['Cantidad_Proyectos'] = gdf_merged['Cantidad_Proyectos'].fillna(0)
    
    # Convertir a GeoJSON para Plotly
    gdf_merged = gdf_merged.to_crs(epsg=4326)
    
    # Crear dos columnas para el layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📍 Mapa de Proyectos por Departamento")
        
        # Crear el mapa de coropletas con Plotly
        fig_mapa = px.choropleth(
            gdf_merged,
            geojson=gdf_merged.geometry,
            locations=gdf_merged.index,
            color='Cantidad_Proyectos',
            hover_name='DPTO_CNMBR',
            hover_data={'Cantidad_Proyectos': True},
            color_continuous_scale='YlOrRd',
            labels={'Cantidad_Proyectos': 'Número de Proyectos'},
            title='Distribución de Proyectos Eólicos por Departamento'
        )
        
        fig_mapa.update_geos(
            fitbounds="locations",
            visible=False
        )
        
        fig_mapa.update_layout(
            height=600,
            margin={"r":0,"t":40,"l":0,"b":0}
        )
        
        st.plotly_chart(fig_mapa, width='stretch')
    
    with col2:
        st.subheader("📊 Proyectos por Año de Publicación")
        
        # Procesar datos por año
        df_excel_clean = df_excel.dropna(subset=['Año de publicación'])
        proyectos_por_año = df_excel_clean.groupby('Año de publicación').size().reset_index(name='Cantidad_Proyectos')
        proyectos_por_año = proyectos_por_año.sort_values('Año de publicación')
        
        # Crear gráfico de línea
        fig_linea = go.Figure()
        
        fig_linea.add_trace(go.Scatter(
            x=proyectos_por_año['Año de publicación'],
            y=proyectos_por_año['Cantidad_Proyectos'],
            mode='lines+markers',
            name='Proyectos',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8, color='#A23B72')
        ))
        
        fig_linea.update_layout(
            title='Evolución Temporal de Proyectos Eólicos',
            xaxis_title='Año de Publicación',
            yaxis_title='Número de Proyectos',
            hovermode='x unified',
            height=600,
            showlegend=False
        )
        
        st.plotly_chart(fig_linea, width='stretch')
    
    # Sección de estadísticas
    st.markdown("---")
    st.subheader("📈 Estadísticas Generales")
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        st.metric("Total de Proyectos", len(df_excel))
    
    with col_stat2:
        st.metric("Departamentos con Proyectos", int(gdf_merged[gdf_merged['Cantidad_Proyectos'] > 0].shape[0]))
    
    with col_stat3:
        años_disponibles = df_excel['Año de publicación'].dropna()
        if len(años_disponibles) > 0:
            st.metric("Rango de Años", f"{int(años_disponibles.min())} - {int(años_disponibles.max())}")
        else:
            st.metric("Rango de Años", "N/A")
    
    with col_stat4:
        dept_max = proyectos_por_depto.iloc[0] if len(proyectos_por_depto) > 0 else None
        if dept_max is not None:
            st.metric("Departamento con Más Proyectos", dept_max['Departamento'].title())
    
    # Tabla detallada
    st.markdown("---")
    st.subheader("📋 Detalle de Proyectos por Departamento")
    
    tabla_resumen = proyectos_por_depto.copy()
    tabla_resumen['Departamento'] = tabla_resumen['Departamento'].str.title()
    tabla_resumen = tabla_resumen.sort_values('Cantidad_Proyectos', ascending=False)
    
    st.dataframe(
        tabla_resumen,
        width='stretch',
        hide_index=True
    )
    
else:
    st.error("⚠️ No se pudieron cargar los datos. Verifica que los archivos existan en las rutas especificadas:")
    st.code("datos\SHP_MGN2018_INTGRD_DEPTO\MGN_ANM_DPTOS.shp")
    st.code("datos\proyectos\proyecto_colombia.xlsx")
    
    st.info("📝 Asegúrate de que:")
    st.markdown("""
    - Los archivos del shapefile estén completos (.shp, .shx, .dbf, .prj)
    - El archivo Excel tenga la columna 'Departamento' y 'Año de publicación'
    - Las rutas de las carpetas sean exactamente como se especifican
    """)

# Pie de página
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Desarrollado con Streamlit 🎈 | Análisis de Proyectos Eólicos en Colombia</p>
    </div>
    """,
    unsafe_allow_html=True
)