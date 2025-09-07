from pathlib import Path
from typing import Any, Callable, Set
import pandas as pd
import pyodbc
import os
import io
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient,BlobServiceClient
from azure.ai.projects import AIProjectClient

from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient


def get_container_client():
    
    tenant_id = os.getenv("Tenant_Id")
    client_id = os.getenv("Client_Id")
    client_secret = os.getenv("Client_Secret")

    # Storage account name
    account_name = "vemaadlsfdpo"

    # Create a credential object
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )

    # Create the BlobServiceClient using the credential
    blob_service_client = BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=credential
    )

    container_name = "hackathon"
    container_client = blob_service_client.get_container_client(container_name)
    return container_client


# def get_container_client():
#     project_endpoint= os.getenv("PROJECT_ENDPOINT")
#     project_client = AIProjectClient(
#         endpoint=project_endpoint,
#         credential=DefaultAzureCredential()
#     )
        
#     storage_connection_name = "vemaadlsfdpo"  # The name from Foundry
#     connection_details = project_client.connections.get(
#         storage_connection_name,
#         include_credentials=True
#     )
   
#     # Use the credentials to create an Azure Storage client
#     storage_connection_key = connection_details.credentials.get("key")
   
#     storage_connection_string = (
#         f"DefaultEndpointsProtocol=https;"
#         f"AccountName={storage_connection_name};"
#         f"AccountKey={storage_connection_key};"
#         f"EndpointSuffix=core.windows.net"
#     )   
    

#     blob_service_client = BlobServiceClient.from_connection_string(conn_str=storage_connection_string)

#     # Now you can use blob_service_client to access your storage account
#     container_name = "hackathon"
#     container_client = blob_service_client.get_container_client(container_name)
#     return container_client
 
def get_employees_by_skillset(skillset: str, availableInDays: int) -> list[dict[int,str, str, str]]:
    """
    This method makes a connection to the SQL db     
    then calls the stored procedure dbo.GetEmployeesForSkill based on the skillset and availability window passed.    
    If stored proc returns rows, then this method returns list of dictionaries with EmployeeId, EmployeeName, Role, Skills 
    else 0 for EmployeeId and null for EmployeeName, Role and Skills.
    """
    
    connection_string = os.getenv("SkillDatabase__sql_connection_string")

    conn = pyodbc.connect(
        connection_string        
    )
    cursor = conn.cursor()    

    cursor.execute("EXEC dbo.GetEmployeesForSkill @Skillset = ?, @AvailableInDays = ?", (skillset,availableInDays))
    rows = cursor.fetchall()
    
    columns = [column[0] for column in cursor.description]   
    conn.commit()
    conn.close()
    if len(rows) > 0:
       return [dict(zip(columns, row)) for row in rows]
    return  [{'EmployeeId': 0, 'EmployeeName': None, 'Role': None, 'Skills': None}]

# def get_employees_by_skillset(skillset: str) -> list[dict[int,str]]:
#     """
#     Looks up the employees for a given skillset in the provided CSV file in the storage account.
#     Returns the distinct list of dictionary of employees based on EmployeeId if found, otherwise 0 for employeeid and 'unknown' for employee name.
#     Dictionary will contain EmployeeId and EmployeeName.
#     """
#     #script_dir = Path(__file__).parent  # Get the directory of the script
#     #csv_path = script_dir / 'employee_skillset.csv'   
#     ## Load the CSV file
#     #df = pd.read_csv(csv_path)    
#     container_client = get_container_client()   
#     blob_data = container_client.download_blob("sourcedata/employee_skillset.csv").readall()
#     # Load into pandas DataFrame
#     df = pd.read_csv(io.BytesIO(blob_data))

#     employees = df[df['SkillsetName'] == skillset][['EmployeeId','EmployeeName']]
#     if len(employees) > 0:        
#         distinct_employees = employees.drop_duplicates(subset='EmployeeId', keep='first')
#         return distinct_employees.to_dict(orient='records')
#     else:    
#         return [{'EmployeeId': 0, 'EmployeeName': 'Unknown'}]
    

def get_employees_util_hours(employee_list: list[int]) -> list[dict[int,int]]:
    """
    Looks up the employees for their utilization hours in the provided CSV file in the Storage Account.
    Returns the employee id and hours if found, otherwise 0 for both EmployeeId and UtilizedHours.
    """
    # script_dir = Path(__file__).parent  # Get the directory of the script
    # csv_path = script_dir / 'employee_util_hours.csv'   
    # # Load the CSV file
    # df = pd.read_csv(csv_path)  

    container_client = get_container_client()   
    blob_data = container_client.download_blob("sourcedata/employee_util_hours.csv").readall()
    # Load into pandas DataFrame
    df = pd.read_csv(io.BytesIO(blob_data))  
    employee_util_hours = df[df['EmployeeId'].isin(employee_list)]
    if not employee_util_hours.empty:
        return  employee_util_hours[['EmployeeId', 'UtilizedHours']].to_dict(orient='records')
    return  [{'EmployeeId': 0, 'UtilizedHours': 0}]

def get_employees_util_target(employee_list: list[int]) -> list[dict[int,int]]:
    """
    Looks up the employees for their utilization target in the provided CSV file in the Storage Account.
    Returns the employee id and target hours if found, otherwise 0 for both EmployeeId and UtilizationTargetHours.
    """
    # script_dir = Path(__file__).parent  # Get the directory of the script
    # csv_path = script_dir / 'employee_target_hours.csv'   
    # # Load the CSV file
    # df = pd.read_csv(csv_path) 
    container_client = get_container_client()   
    blob_data = container_client.download_blob("sourcedata/employee_target_hours.csv").readall()
    # Load into pandas DataFrame
    df = pd.read_csv(io.BytesIO(blob_data))    
    employee_target_hours = df[df['EmployeeId'].isin(employee_list)]
    if not employee_target_hours.empty:
        return  employee_target_hours[['EmployeeId', 'UtilizationTargetHours']].to_dict(orient='records')
    return  [{'EmployeeId': 0, 'UtilizationTargetHours': 0}]


def get_employees_leave_balance(employee_list: list[int]) -> list[dict[int,int]]:
    """
    This method makes a connection to the SQL db 
    inserts the list of employees passed to a temp table in SQL db
    then calls the stored procedure dbo.GetEmployeeLeaves which uses this temp table 
    to get the number of leave days for each employee.
    If stored proc returns rows, then this method returns list of dictionaries with EmployeeId and LeaveBalance.
    else 0 for both EmployeeId and LeaveBalance.
    """
    
    connection_string = os.getenv("LeaveDatabase__sql_connection_string")

    conn = pyodbc.connect(
        connection_string        
    )
    cursor = conn.cursor()

    cursor.execute("""
    IF OBJECT_ID('tempdb..#EmployeeTemp') IS NOT NULL DROP TABLE #EmployeeTemp;
    CREATE TABLE #EmployeeTemp (
        EmployeeID INT    
    );
    """)
    conn.commit()
    employees = [(emp_id,) for emp_id in employee_list]    

    cursor.executemany("""
    INSERT INTO #EmployeeTemp (EmployeeID)
    VALUES (?)
    """, employees)
    conn.commit()

    cursor.execute("EXEC dbo.GetEmployeeLeaves")
    rows = cursor.fetchall()

    columns = [column[0] for column in cursor.description]   
    conn.commit()
    conn.close()
    if len(rows) > 0:
       return [dict(zip(columns, row)) for row in rows]
    return  [{'EmployeeId': 0, 'LeaveBalance': 0}]

    # Add all functions to the callable set
user_functions: Set[Callable[..., Any]] = {
    get_employees_by_skillset,
    get_employees_util_hours,
    get_employees_util_target,
    get_employees_leave_balance
}


