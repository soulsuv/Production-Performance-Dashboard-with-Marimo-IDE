import marimo

__generated_with = "0.12.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    import marimo as mo
    return go, mo, np, pd, px


@app.cell
def _(mo):

    # File paths
    production_file_path = mo.ui.text(
        label="Enter the file path for production data (Excel file):",
        value="",
        placeholder="e.g., C:/path/to/production_data.xlsx"
    )

    coordinates_file_path = mo.ui.text(
        label="Enter the file path for coordinates data (Excel file, optional):",
        value="",
        placeholder="e.g., C:/path/to/well_coordinates.xlsx"
    )

    # Sheet names
    production_sheet_name = mo.ui.text(
        label="Production data sheet name:",
        value="",
        placeholder="e.g., MonthProd"
    )
    pressure_sheet_name = mo.ui.text(
        label="Pressure data sheet name:",
        value="",
        placeholder="e.g., Pressure"
    )
    mer_sheet_name = mo.ui.text(
        label="MER/well test data sheet name:",
        value="",
        placeholder="e.g., Well test"
    )

    # Common column
    strings_header_name = mo.ui.text(
        label="Strings column (e.g., UNIQUEID):",
        value="",
        placeholder="e.g., UNIQUEID"
    )

    # Plot settings
    min_wor_y = mo.ui.number(
        label="Min y-axis WOR/WOR' (log):",
        value=-5,
        start=-50,
        stop=0,
        step=1
    )
    min_gor_y = mo.ui.number(
        label="Min y-axis GOR/GOR' (log):",
        value=-5,
        start=-50,
        stop=0,
        step=1
    )
    wor_log_threshold_input = mo.ui.number(
        label="Min log10 threshold for WOR'_Positives:",
        start=-20,
        stop=0,
        step=0.1,
        value=-5
    )
    gor_log_threshold_input = mo.ui.number(
        label="Min log10 threshold for GOR'_Positives:",
        start=-20,
        stop=0,
        step=0.1,
        value=-5
    )
    ma_window_size = mo.ui.dropdown(
        options=[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        value=2,
        label="Moving Average Window Size"
    )
    field_level_ma = mo.ui.checkbox(
        label="Use Field-Level Moving Average (for all selected strings)",
        value=False
    )

    # Column naming instructions
    instructions = mo.md("""
    ### Expected Column Names
    Ensure your Excel sheets contain the following columns (case-insensitive, e.g., 'bopd' or 'BOPD' works):

    **Monthly Production Data**:
    - UNIQUEID (e.g., well identifier)
    - Date (MM/DD/YYYY)
    - BOPD (Oil production, bbl/day)
    - Days produced
    - GR (Gas rate, mmscf/day)
    - BWPD (Water production, bbl/day)
    - Oil Rate (stb/m) (optional)
    - Water(bbl/m) (optional)
    - choke (optional)
    - GOR (optional, will be validated or calculated)

    **Pressure Data**:
    - UNIQUEID
    - Date (MM/DD/YYYY)
    - Pressure (psi)

    **MER/Well Test Data**:
    - UNIQUEID
    - Date (MM/DD/YYYY)
    - Test BOPD (Oil rate, bbl/day)
    - Test GOR (scf/stb)
    - Test BWPD (Water rate, bbl/day)
    - ChokeSize (/64)

    **Coordinates Data** (if provided):
    - UNIQUEID
    - X (X-coordinate)
    - Y (Y-coordinate)

    The code will automatically detect these columns (case-insensitive) and process the data accordingly.
    """)

    # Display inputs
    mo.vstack([
        instructions,
        mo.md("### File Paths"),
        production_file_path, coordinates_file_path,
        mo.md("### Sheet Names"),
        production_sheet_name, pressure_sheet_name, mer_sheet_name,
        mo.md("### Common Column"),
        strings_header_name,
        mo.md("### Plot Settings"),
        min_wor_y, min_gor_y, wor_log_threshold_input, gor_log_threshold_input, ma_window_size, field_level_ma
    ])
    return (
        coordinates_file_path,
        field_level_ma,
        gor_log_threshold_input,
        instructions,
        ma_window_size,
        mer_sheet_name,
        min_gor_y,
        min_wor_y,
        pressure_sheet_name,
        production_file_path,
        production_sheet_name,
        strings_header_name,
        wor_log_threshold_input,
    )


@app.cell
def _(
    coordinates_file_path,
    mer_sheet_name,
    np,
    pd,
    pressure_sheet_name,
    production_file_path,
    production_sheet_name,
    strings_header_name,
):
    # Load data
    production_data = pd.read_excel(production_file_path.value, sheet_name=production_sheet_name.value)
    pressure_data = pd.read_excel(production_file_path.value, sheet_name=pressure_sheet_name.value)
    mer_data = pd.read_excel(production_file_path.value, sheet_name=mer_sheet_name.value)

    # Function to find column by case-insensitive partial match
    def find_column(df, possible_names):
        for col in df.columns:
            if col.lower() in [name.lower() for name in possible_names]:
                return col
        return None

    # Define expected columns (case-insensitive)
    prod_columns = {
        'UNIQUEID': [strings_header_name.value],
        'Date': ['date (mm/dd/yyyy)', 'date'],
        'BOPD': ['bopd', 'oil production', 'oil rate (bbl/day)'],
        'Days produced': ['days produced', 'producing days'],
        'GR': ['gr', 'gas rate', 'mmscf/day'],
        'BWPD': ['bwpd', 'water production', 'water rate (bbl/day)'],
        'Oil Rate (stb/m)': ['oil rate (stb/m)', 'oil (stb/month)'],
        'Water(bbl/m)': ['water(bbl/m)', 'water (bbl/month)'],
        'choke': ['choke', 'choke size'],
        'GOR': ['gor', 'gas oil ratio']
    }
    pressure_columns = {
        'UNIQUEID': [strings_header_name.value],
        'Date': ['date (mm/dd/yyyy)', 'date'],
        'Pressure (psi)': ['pressure (psi)', 'pressure']
    }
    mer_columns = {
        'UNIQUEID': [strings_header_name.value],
        'Date': ['date (mm/dd/yyyy)', 'date'],
        'Test BOPD': ['test bopd', 'net_oil(bopd)', 'oil test'],
        'Test GOR': ['test gor', 'gor'],
        'Test BWPD': ['test bwpd', 'water(bpd)', 'water test'],
        'ChokeSize (/64)': ['chokesize (/64)', 'choke size']
    }
    coord_columns = {
        'UNIQUEID': [strings_header_name.value],
        'X': ['x', 'x coordinate'],
        'Y': ['y', 'y coordinate']
    }

    # Map columns for each dataset
    def map_columns(df, column_map):
        rename_dict = {}
        for standard_name, possible_names in column_map.items():
            found_col = find_column(df, possible_names)
            if found_col:
                rename_dict[found_col] = standard_name
        return df.rename(columns=rename_dict)

    # Apply column mapping
    production_data = map_columns(production_data, prod_columns)
    pressure_data = map_columns(pressure_data, pressure_columns)
    mer_data = map_columns(mer_data, mer_columns)

    # Standardize dates
    def standardize_dates(df, date_col='Date'):
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            return df.dropna(subset=[date_col])
        return df

    # Apply date standardization
    production_data = standardize_dates(production_data)
    pressure_data = standardize_dates(pressure_data)
    mer_data = standardize_dates(mer_data)

    # Debug: Print columns
    print("Production data columns:", production_data.columns.tolist())
    print("Pressure data columns:", pressure_data.columns.tolist())
    print("MER data columns:", mer_data.columns.tolist())

    # Check for missing critical columns
    required_prod_cols = ['Date', 'BOPD', 'Days produced', 'UNIQUEID']
    missing_prod = [col for col in required_prod_cols if col not in production_data.columns]
    if missing_prod:
        raise ValueError(f"Missing critical columns in production data: {missing_prod}")

    # Compute Cumulative Producing Days
    production_data = production_data.sort_values(['UNIQUEID', 'Date'])
    production_data['Cumulative Days Produced'] = production_data.groupby('UNIQUEID')['Days produced'].cumsum()

    # Calculate total oil
    total_oil_per_string = (production_data.groupby('UNIQUEID')
                           .apply(lambda x: (x['BOPD'] * x['Days produced']).sum())
                           .reset_index(name='Total Oil (stb)'))

    # Merge pressure data
    if 'Pressure (psi)' in pressure_data.columns:
        production_data = production_data.merge(
            pressure_data[['UNIQUEID', 'Date', 'Pressure (psi)']],
            on=['UNIQUEID', 'Date'],
            how='left'
        )

    # Validate or calculate GOR
    if 'GR' in production_data.columns and 'BOPD' in production_data.columns:
        calculated_gor = np.where(
            production_data['BOPD'] > 0,
            (production_data['GR'] * 1_000_000) / production_data['BOPD'],
            0
        )
        if 'GOR' in production_data.columns and not production_data['GOR'].isna().all():
            print("Validating pre-calculated GOR...")
            # Check if pre-calculated GOR matches computed GOR (within 5% tolerance)
            valid_gor = np.isclose(
                production_data['GOR'].replace([np.inf, -np.inf], np.nan).fillna(0),
                calculated_gor,
                rtol=0.05
            ).mean() > 0.95  # 95% of values should match
            if valid_gor:
                print("Pre-calculated GOR is valid, using it.")
                production_data['GOR'] = np.where(
                    production_data['BOPD'] == 0,
                    0,
                    production_data['GOR'].replace([np.inf, -np.inf], np.nan)
                )
            else:
                print("Pre-calculated GOR is inconsistent, recalculating.")
                production_data['GOR'] = calculated_gor
        else:
            print("Calculating GOR (scf/stb).")
            production_data['GOR'] = calculated_gor

    # Calculate WOR
    if all(col in production_data.columns for col in ['Oil Rate (stb/m)', 'Water(bbl/m)']):
        production_data['WOR'] = np.where(
            production_data['Oil Rate (stb/m)'] > 0,
            production_data['Water(bbl/m)'] / production_data['Oil Rate (stb/m)'],
            0
        )

    # Calculate derivatives
    if 'GOR' in production_data.columns:
        production_data['GOR_Deriv'] = np.where(
            production_data['Cumulative Days Produced'].diff() > 0,
            production_data.groupby('UNIQUEID')['GOR'].diff() / production_data.groupby('UNIQUEID')['Cumulative Days Produced'].diff(),
            0
        )
        production_data['GOR_Deriv_Pos'] = np.where(production_data['GOR_Deriv'] > 0, production_data['GOR_Deriv'], np.nan)

    if 'WOR' in production_data.columns:
        production_data['WOR_Deriv'] = np.where(
            production_data['Cumulative Days Produced'].diff() > 0,
            production_data.groupby('UNIQUEID')['WOR'].diff() / production_data.groupby('UNIQUEID')['Cumulative Days Produced'].diff(),
            0
        )
        production_data['WOR_Deriv_Pos'] = np.where(production_data['WOR_Deriv'] > 0, production_data['WOR_Deriv'], np.nan)

    # Add month for choke matching
    if 'Date' in mer_data.columns:
        mer_data['month'] = mer_data['Date'].dt.to_period('M')

    # Choke matching
    if 'choke' in production_data.columns and 'ChokeSize (/64)' in mer_data.columns:
        choke_mapping = production_data[['UNIQUEID', 'Date', 'choke']].copy()
        choke_mapping['month'] = choke_mapping['Date'].dt.to_period('M')
        choke_mapping = choke_mapping.drop(columns=['Date']).drop_duplicates()
        choke_mapping = choke_mapping.set_index(['UNIQUEID', 'month'])['choke'].to_dict()
        mer_data['choke_match'] = mer_data.apply(
            lambda row: choke_mapping.get((row['UNIQUEID'], row['month'])) == row['ChokeSize (/64)'],
            axis=1
        )
        filtered_mer_data = mer_data[mer_data['choke_match']].drop(columns=['choke_match', 'month'])
    else:
        filtered_mer_data = mer_data.copy()
        print("Warning: Choke matching skipped due to missing 'choke' or 'ChokeSize (/64)' columns.")

    # Load coordinates
    coordinates_data = pd.DataFrame()
    if coordinates_file_path.value.strip():
        xl = pd.ExcelFile(coordinates_file_path.value)
        coords_list = []
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(coordinates_file_path.value, sheet_name=sheet_name)
            df[strings_header_name.value] = sheet_name
            coords_list.append(df)

        if coords_list:
            coordinates_data = pd.concat(coords_list, ignore_index=True)
            coordinates_data = map_columns(coordinates_data, coord_columns)
            coordinates_data = coordinates_data.merge(
                total_oil_per_string[['UNIQUEID', 'Total Oil (stb)']],
                on='UNIQUEID',
                how='left'
            )
            coordinates_data['Total Oil (stb)'] = coordinates_data['Total Oil (stb)'].fillna(0)
            print("Coordinates data columns:", coordinates_data.columns.tolist())
            print("Coordinates data preview:", coordinates_data.head())
        else:
            print("No sheets found in coordinates file.")
    else:
        print("No coordinates file provided.")
    return (
        calculated_gor,
        choke_mapping,
        coord_columns,
        coordinates_data,
        coords_list,
        df,
        filtered_mer_data,
        find_column,
        map_columns,
        mer_columns,
        mer_data,
        missing_prod,
        pressure_columns,
        pressure_data,
        prod_columns,
        production_data,
        required_prod_cols,
        sheet_name,
        standardize_dates,
        total_oil_per_string,
        valid_gor,
        xl,
    )


@app.cell
def _(mo, production_data):
    string_options = ['All'] + sorted(production_data['UNIQUEID'].unique().tolist())
    selected_strings = mo.ui.array(
        [mo.ui.checkbox(label=opt, value=(opt == 'All')) for opt in string_options],
        label="Select strings to plot:"
    )
    selected_strings
    return selected_strings, string_options


@app.cell
def _(mo, production_data, selected_strings, string_options):
    # Compute selected and filtered_data
    selected = [string_options[i] for i, checked in enumerate(selected_strings.value) if checked]
    filtered_data = production_data if 'All' in selected else production_data[production_data['UNIQUEID'].isin(selected)]
    mo.md(f"**Selected strings**: {', '.join(selected) if selected != ['All'] else 'All Strings'}")
    return filtered_data, selected


@app.cell
def _(find_column, go, mo, np, selected_strings, string_options):
    def create_deriv_plot(data, strings_header='UNIQUEID', y_cols=['GOR', 'GOR_Deriv_Pos'], title="GOR vs GOR' (Positive)", min_y=-5, x_col='Cumulative Days Produced', log_threshold=-5, ma_window=5, field_level_ma=False):
        selected = [string_options[i] for i, checked in enumerate(selected_strings.value) if checked]
        filtered_data = data if 'All' in selected else data[data[strings_header].isin(selected)]
        columns_to_keep = [x_col, strings_header] + y_cols
        filtered_data = filtered_data[columns_to_keep].dropna(subset=y_cols)
    
        # Apply log threshold filters
        plot_data = filtered_data.copy()
        if y_cols[1] in plot_data.columns:
            plot_data = plot_data[np.log10(plot_data[y_cols[1]].replace(0, np.nan)) >= log_threshold]
        if y_cols[0] in plot_data.columns:
            plot_data = plot_data[np.log10(plot_data[y_cols[0]].replace(0, np.nan)) >= min_y]
    
        # Calculate moving averages in log domain
        if y_cols[0] in plot_data.columns and y_cols[1] in plot_data.columns:
            # Sort by Cumulative Days Produced to ensure correct rolling order
            plot_data = plot_data.sort_values([strings_header, x_col])
            # Compute log10 of GOR/WOR and GOR'/WOR'
            plot_data[f'log_{y_cols[0]}'] = np.log10(plot_data[y_cols[0]].replace(0, np.nan))
            plot_data[f'log_{y_cols[1]}'] = np.log10(plot_data[y_cols[1]].replace(0, np.nan))
        
            if field_level_ma:
                # Field-level MA: Aggregate log(GOR/WOR) and log(GOR'/WOR') by Cumulative Days Produced
                agg_data = plot_data.groupby(x_col)[[f'log_{y_cols[0]}', f'log_{y_cols[1]}']].mean().reset_index()
                agg_data[f'log_{y_cols[0]}_MA{ma_window}'] = agg_data[f'log_{y_cols[0]}'].rolling(ma_window, min_periods=1).mean()
                agg_data[f'log_{y_cols[1]}_MA{ma_window}'] = agg_data[f'log_{y_cols[1]}'].rolling(ma_window, min_periods=1).mean()
                # Convert MA back to linear domain for plotting
                agg_data[f'{y_cols[0]}_MA{ma_window}'] = np.power(10, agg_data[f'log_{y_cols[0]}_MA{ma_window}'])
                agg_data[f'{y_cols[1]}_MA{ma_window}'] = np.power(10, agg_data[f'log_{y_cols[1]}_MA{ma_window}'])
                # Merge back to plot_data
                plot_data = plot_data.merge(
                    agg_data[[x_col, f'{y_cols[0]}_MA{ma_window}', f'{y_cols[1]}_MA{ma_window}']],
                    on=x_col,
                    how='left'
                )
            else:
                # Per-string MA: Compute MA on log(GOR/WOR) and log(GOR'/WOR') per UNIQUEID
                plot_data[f'log_{y_cols[0]}_MA{ma_window}'] = plot_data.groupby(strings_header)[f'log_{y_cols[0]}'].transform(
                    lambda x: x.rolling(ma_window, min_periods=1).mean()
                )
                plot_data[f'log_{y_cols[1]}_MA{ma_window}'] = plot_data.groupby(strings_header)[f'log_{y_cols[1]}'].transform(
                    lambda x: x.rolling(ma_window, min_periods=1).mean()
                )
                # Convert MA back to linear domain for plotting
                plot_data[f'{y_cols[0]}_MA{ma_window}'] = np.power(10, plot_data[f'log_{y_cols[0]}_MA{ma_window}'])
                plot_data[f'{y_cols[1]}_MA{ma_window}'] = np.power(10, plot_data[f'log_{y_cols[1]}_MA{ma_window}'])
    
        # Create plot
        fig = go.Figure()
        # Original GOR or WOR
        fig.add_trace(go.Scatter(
            x=plot_data[x_col],
            y=plot_data[y_cols[0]],
            mode='markers',
            name=y_cols[0],
            marker=dict(size=8, color='green' if 'GOR' in y_cols[0] else 'blue'),
            text=plot_data[strings_header]
        ))
        # GOR/WOR Moving Average
        if f'{y_cols[0]}_MA{ma_window}' in plot_data.columns:
            if field_level_ma:
                agg_data = plot_data[[x_col, f'{y_cols[0]}_MA{ma_window}']].drop_duplicates()
                fig.add_trace(go.Scatter(
                    x=agg_data[x_col],
                    y=agg_data[f'{y_cols[0]}_MA{ma_window}'],
                    mode='lines',
                    name=f'{y_cols[0]} ({ma_window}-point Field MA)',
                    line=dict(color='darkgreen' if 'GOR' in y_cols[0] else 'darkblue', dash='dash'),
                ))
            else:
                for string in plot_data[strings_header].unique():
                    string_data = plot_data[plot_data[strings_header] == string]
                    fig.add_trace(go.Scatter(
                        x=string_data[x_col],
                        y=string_data[f'{y_cols[0]}_MA{ma_window}'],
                        mode='lines',
                        name=f'{y_cols[0]} ({ma_window}-point MA) - {string}',
                        line=dict(color='darkgreen' if 'GOR' in y_cols[0] else 'darkblue', dash='dash'),
                        text=string_data[strings_header]
                    ))
        # Derivative (GOR_Deriv_Pos or WOR_Deriv_Pos)
        fig.add_trace(go.Scatter(
            x=plot_data[x_col],
            y=plot_data[y_cols[1]],
            mode='markers',
            name=y_cols[1],
            marker=dict(size=8, color='red'),
            text=plot_data[strings_header]
        ))
        # Derivative Moving Average
        if f'{y_cols[1]}_MA{ma_window}' in plot_data.columns:
            if field_level_ma:
                agg_data = plot_data[[x_col, f'{y_cols[1]}_MA{ma_window}']].drop_duplicates()
                fig.add_trace(go.Scatter(
                    x=agg_data[x_col],
                    y=agg_data[f'{y_cols[1]}_MA{ma_window}'],
                    mode='lines',
                    name=f'{y_cols[1]} ({ma_window}-point Field MA)',
                    line=dict(color='darkred', dash='dot'),
                ))
            else:
                for string in plot_data[strings_header].unique():
                    string_data = plot_data[plot_data[strings_header] == string]
                    fig.add_trace(go.Scatter(
                        x=string_data[x_col],
                        y=string_data[f'{y_cols[1]}_MA{ma_window}'],
                        mode='lines',
                        name=f'{y_cols[1]} ({ma_window}-point MA) - {string}',
                        line=dict(color='darkred', dash='dot'),
                        text=string_data[strings_header]
                    ))
        fig.update_layout(
            yaxis_title=f"{title.split()[0]} / {title.split()[2]}",
            xaxis_title="Cumulative Days Produced (log scale)",
            xaxis=dict(type='log'),
            yaxis=dict(type='log', range=[min_y, None]),
            legend_title="Metric",
            title=title
        )
    
        return mo.ui.plotly(fig)

    def create_allocation_plot(data, mer_data, strings_header='UNIQUEID'):
        selected = [string_options[i] for i, checked in enumerate(selected_strings.value) if checked]
        filtered_data = data if 'All' in selected else data[data[strings_header].isin(selected)]
        filtered_mer = mer_data if 'All' in selected else mer_data[mer_data[strings_header].isin(selected)]
    
        fig = go.Figure()
        for string in filtered_data[strings_header].unique():
            string_data = filtered_data[filtered_data[strings_header] == string]
            fig.add_trace(go.Scatter(
                x=string_data['Date'],
                y=string_data['BOPD'],
                mode='lines',
                name=f'{string} Oil Rate',
                line=dict(color='red')
            ))
            if 'BWPD' in string_data.columns:
                fig.add_trace(go.Scatter(
                    x=string_data['Date'],
                    y=string_data['BWPD'],
                    mode='lines',
                    name=f'{string} Water Rate',
                    line=dict(color='blue')
                ))
            if 'GOR' in string_data.columns:
                fig.add_trace(go.Scatter(
                    x=string_data['Date'],
                    y=string_data['GOR'],
                    mode='lines',
                    name=f'{string} GOR',
                    line=dict(color='green'),
                    yaxis='y2'
                ))
    
        if 'Test BOPD' in filtered_mer.columns:
            fig.add_trace(go.Scatter(
                x=filtered_mer['Date'],
                y=filtered_mer['Test BOPD'],
                mode='markers',
                name='Test Oil Rate',
                marker=dict(size=8, color='red')
            ))
        if 'Test BWPD' in filtered_mer.columns:
            fig.add_trace(go.Scatter(
                x=filtered_mer['Date'],
                y=filtered_mer['Test BWPD'],
                mode='markers',
                name='Test Water Rate',
                marker=dict(size=8, color='blue')
            ))
        if 'Test GOR' in filtered_mer.columns:
            fig.add_trace(go.Scatter(
                x=filtered_mer['Date'],
                y=filtered_mer['Test GOR'],
                mode='markers',
                name='Test GOR',
                marker=dict(size=8, color='green'),
                yaxis='y2'
            ))
        fig.update_layout(
            yaxis_title="Oil/Water Rate (stb/d, bbl/d)",
            yaxis2=dict(title="GOR (scf/stb)", overlaying='y', side='right'),
            xaxis_title="Date",
            legend_title="Data Type",
            title="Production Allocation vs Well Test",
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1.0,
                xanchor="left",
                x=1.3,
                font=dict(size=10)
            ),
            margin=dict(r=100),
            width=900,
            height=500
        )
        return mo.ui.plotly(fig)

    def create_oil_rate_plot(data, strings_header='UNIQUEID'):
        selected = [string_options[i] for i, checked in enumerate(selected_strings.value) if checked]
        filtered_data = data if 'All' in selected else data[data[strings_header].isin(selected)]
    
        if 'BOPD' not in filtered_data.columns:
            raise KeyError("Column 'BOPD' not found in the data.")
        days_produced_col = find_column(filtered_data, ['Days Produced', 'days produced', 'producing days'])
        if days_produced_col is None:
            raise KeyError("Column for 'Days Produced' not found. Expected one of: 'Days Produced', 'days produced', 'producing days'.")
    
        filtered_data = filtered_data.copy()
        filtered_data['Oil Produced'] = filtered_data['BOPD'] * filtered_data[days_produced_col]
    
        fig = go.Figure()
        for string in filtered_data[strings_header].unique():
            string_data = filtered_data[filtered_data[strings_header] == string]
            fig.add_trace(go.Scatter(
                x=string_data['Cumulative Days Produced'],
                y=string_data['BOPD'],
                mode='lines',
                name=f'{string} Oil Rate',
                line=dict(color='red')
            ))
    
        sum_data = filtered_data.groupby('Cumulative Days Produced')['Oil Produced'].sum().cumsum().reset_index()
        sum_data = sum_data.rename(columns={'Oil Produced': 'Cumulative Oil (stb)'})
        fig.add_trace(go.Scatter(
            x=sum_data['Cumulative Days Produced'],
            y=sum_data['Cumulative Oil (stb)'],
            mode='lines',
            name='Cumulative Oil',
            line=dict(dash='dash', color='red'),
            yaxis='y2'
        ))
        fig.update_layout(
            yaxis_title="Oil Rate (stb/d)",
            yaxis2=dict(title="Cumulative Oil (stb)", overlaying='y', side='right'),
            xaxis_title="Cumulative Days Produced",
            title="Oil Rate with Cumulative Sum",
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1.0,
                xanchor="left",
                x=1.3,
                font=dict(size=10)
            ),
            margin=dict(r=100),
            width=900,
            height=500
        )
        return mo.ui.plotly(fig)

    def create_gor_watercut_plot(data, strings_header='UNIQUEID'):
        selected = [string_options[i] for i, checked in enumerate(selected_strings.value) if checked]
        filtered_data = data if 'All' in selected else data[data[strings_header].isin(selected)]
    
        days_produced_col = find_column(filtered_data, ['Days Produced', 'days produced', 'producing days'])
        if days_produced_col is None:
            raise KeyError("Column for 'Days Produced' not found in gor_watercut_plot. Expected one of: 'Days Produced', 'days produced', 'producing days'.")
    
        plot_data = filtered_data.copy()
        if 'BOPD' in plot_data.columns and days_produced_col in plot_data.columns:
            plot_data['Oil Produced'] = plot_data['BOPD'] * plot_data[days_produced_col]
        else:
            plot_data['Oil Produced'] = 0
        if 'GR' in plot_data.columns and days_produced_col in plot_data.columns:
            plot_data['Gas Produced'] = plot_data['GR'] * 1_000_000 * plot_data[days_produced_col]
        else:
            plot_data['Gas Produced'] = 0
        if 'BWPD' in plot_data.columns and days_produced_col in plot_data.columns:
            plot_data['Water Produced'] = plot_data['BWPD'] * plot_data[days_produced_col]
        else:
            plot_data['Water Produced'] = 0
    
        plot_data = plot_data.groupby('Date').agg({
            'Oil Produced': 'sum',
            'Gas Produced': 'sum',
            'Water Produced': 'sum'
        }).reset_index()
    
        plot_data['Field GOR'] = np.where(
            plot_data['Oil Produced'] > 0,
            plot_data['Gas Produced'] / plot_data['Oil Produced'],
            0
        )
        plot_data['Field Water Cut'] = np.where(
            (plot_data['Oil Produced'] + plot_data['Water Produced']) > 0,
            (plot_data['Water Produced'] / (plot_data['Oil Produced'] + plot_data['Water Produced'])) * 100,
            0
        )
    
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=plot_data['Date'],
            y=plot_data['Field GOR'],
            mode='lines',
            name='Field GOR',
            line=dict(color='green')
        ))
        fig.add_trace(go.Scatter(
            x=plot_data['Date'],
            y=plot_data['Field Water Cut'],
            mode='lines',
            name='Field Water Cut (%)',
            line=dict(color='blue'),
            yaxis='y2'
        ))
        fig.update_layout(
            title="Field GOR and Water Cut vs Time",
            xaxis_title="Date",
            yaxis_title="Field GOR (scf/stb)",
            yaxis2=dict(title="Field Water Cut (%)", overlaying='y', side='right'),
            legend_title="Metric",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.5,
                xanchor="center",
                x=0.5
            )
        )
        return mo.ui.plotly(fig)
    return (
        create_allocation_plot,
        create_deriv_plot,
        create_gor_watercut_plot,
        create_oil_rate_plot,
    )


@app.cell
def _(
    coordinates_data,
    create_allocation_plot,
    create_deriv_plot,
    create_gor_watercut_plot,
    create_oil_rate_plot,
    field_level_ma,
    filtered_data,
    filtered_mer_data,
    find_column,
    gor_log_threshold_input,
    ma_window_size,
    min_gor_y,
    min_wor_y,
    mo,
    np,
    production_data,
    px,
    selected,
    selected_strings,
    wor_log_threshold_input,
):
    # Get log thresholds
    wor_log_threshold_value = wor_log_threshold_input.value
    gor_log_threshold_value = gor_log_threshold_input.value
    ma_window_value = ma_window_size.value
    field_level_ma_value = field_level_ma.value

    # Spatial plot
    if not coordinates_data.empty and {'X', 'Y', 'UNIQUEID'}.issubset(coordinates_data.columns):
        filtered_coordinates = coordinates_data if 'All' in selected else coordinates_data[coordinates_data['UNIQUEID'].isin(selected)]
    
        fig_map = px.scatter(
            filtered_coordinates,
            x='X',
            y='Y',
            size='Total Oil (stb)',
            color='UNIQUEID',
            title="String Locations (Size = Total Oil Production)",
            hover_data=['UNIQUEID', 'Total Oil (stb)'],
            size_max=50
        )
        map_plot = mo.ui.plotly(fig_map)
    else:
        map_plot = mo.md("⚠️ No coordinate data available or missing X/Y/UNIQUEID columns")



    if 'BOPD' not in filtered_data.columns:
        raise KeyError("Column 'BOPD' not found in the data.")
    days_produced_col = find_column(filtered_data, ['Days Produced', 'days produced', 'producing days'])
    if days_produced_col is None:
        raise KeyError("Column for 'Days Produced' not found in summary stats. Expected one of: 'Days Produced', 'days produced', 'producing days'.")

    total_oil = (filtered_data['BOPD'] * filtered_data[days_produced_col]).sum()
    avg_watercut = (np.where(
        (filtered_data['BOPD'] + filtered_data['BWPD']) > 0,
        (filtered_data['BWPD'] / (filtered_data['BOPD'] + filtered_data['BWPD'])) * 100,
        0
    ).mean() if 'BWPD' in filtered_data.columns else 0)
    avg_gor = filtered_data['GOR'].mean() if 'GOR' in filtered_data.columns else 0
    max_pressure = filtered_data['Pressure (psi)'].max() if 'Pressure (psi)' in filtered_data.columns else 0

    stats_card = mo.md(
        f"""
        ## Summary Statistics
        **Strings:** {', '.join(selected) if selected != ['All'] else 'All Strings'}
        - **Total Oil Production**: {total_oil:,.0f} STB
        - **Avg Oil Rate**: {filtered_data['BOPD'].mean():.1f} stb/d
        - **Avg Watercut**: {avg_watercut:.1f}%
        - **Avg GOR**: {avg_gor:.1f} scf/stb
        - **Max Pressure**: {max_pressure:.1f} psi
        """
    ).style({"border": "1px solid #ccc", "padding": "10px"})

    # Dashboard
    dashboard = mo.ui.tabs({
        "Overview": [
            selected_strings,
            stats_card,
            map_plot,
            create_allocation_plot(production_data, filtered_mer_data),
            create_oil_rate_plot(production_data)
        ],
        "Diagnostics": [
            create_gor_watercut_plot(production_data),
            create_deriv_plot(
                production_data, 
                y_cols=['GOR', 'GOR_Deriv_Pos'], 
                title="GOR vs GOR' (Positive)", 
                min_y=min_gor_y.value,
                log_threshold=gor_log_threshold_value,
                ma_window=ma_window_value,
                field_level_ma=field_level_ma_value
            ),
            create_deriv_plot(
                production_data, 
                y_cols=['WOR', 'WOR_Deriv_Pos'], 
                title="WOR vs WOR' (Positive)", 
                min_y=min_wor_y.value,
                log_threshold=wor_log_threshold_value,
                ma_window=ma_window_value,
                field_level_ma=field_level_ma_value
            )
        ],
        "Data": [
            mo.ui.table(
                filtered_data[[col for col in ['UNIQUEID', 'Date', 'BOPD', 'GOR', 'BWPD', 'Pressure (psi)'] if col in filtered_data.columns]].head(100)
            ),
            mo.download(
                data=filtered_data.to_csv(index=False),
                filename=f"production_data_{'_'.join(selected) or 'all'}.csv",
                label="📥 Download Filtered Data"
            )
        ]
    })
    dashboard
    return (
        avg_gor,
        avg_watercut,
        dashboard,
        days_produced_col,
        field_level_ma_value,
        fig_map,
        filtered_coordinates,
        gor_log_threshold_value,
        ma_window_value,
        map_plot,
        max_pressure,
        stats_card,
        total_oil,
        wor_log_threshold_value,
    )


if __name__ == "__main__":
    app.run()
