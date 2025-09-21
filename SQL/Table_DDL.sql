create table dbo.EmployeeDetails
(
EmployeeId         int,
EmployeeName       varchar(100),
Designation        varchar(100),
Manager            varchar(100)
)

create table dbo.EmployeeProjectDetails
(
EmployeeId         int,
ProjectName        varchar(200),
StartDate          date,
EndDate            date,
Status             varchar(50)
)


create table dbo.EmployeeSkillsTest2
(
EmployeeId         int,
EmployeeName       varchar(100),
Role               varchar(200),
Skills              varchar(2000),
RoleEmbedding   vector(1536),
SkillsEmbedding vector(1536)
)
