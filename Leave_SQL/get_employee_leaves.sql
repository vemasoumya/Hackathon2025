alter  proc dbo.GetEmployeeLeaves
as 
begin 
    select t1.EmployeeId, sum(NumWorkingDays) as LeaveBalance from 
	dbo.LeaveRequests t1 
	join #EmployeeTemp t2 
	on t1.EmployeeId = t2.EmployeeId
	where StartDate > getdate()
	group by t1.EmployeeId

end 
