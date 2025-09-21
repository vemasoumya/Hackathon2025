DROP TABLE IF EXISTS #MYTEMP 
DECLARE @EmployeeId int
DECLARE @Role varchar(100)
declare @text nvarchar(max);
declare @vector1 vector(1536);
declare @vector2 vector(1536);
SELECT * INTO #MYTEMP FROM dbo.EmployeeSkillsTest2
SELECT @EmployeeId = EmployeeId, @Role = Role   FROM #MYTEMP
SELECT TOP(1) @EmployeeId = EmployeeId , @Role = Role FROM #MYTEMP
WHILE @@ROWCOUNT <> 0
BEGIN
    set @text = (SELECT   
					Role from 
					dbo.EmployeeSkillsTest2 
				 where EmployeeId = @EmployeeId  and Role = @Role);
    exec dbo.create_embeddings @text, @vector1 output;
    update dbo.EmployeeSkillsTest2 set [RoleEmbedding] = @vector1 where EmployeeId = @EmployeeId  and Role = @Role;
	set @text = (SELECT   
					Skills from 
					dbo.EmployeeSkillsTest2 
				 where EmployeeId = @EmployeeId  and Role = @Role);
    exec dbo.create_embeddings @text, @vector2 output;
    update dbo.EmployeeSkillsTest2 set [SkillsEmbedding] = @vector2 where EmployeeId = @EmployeeId  and Role = @Role;
    DELETE FROM #MYTEMP WHERE EmployeeId = @EmployeeId  and Role = @Role 
    SELECT TOP(1) @EmployeeId = EmployeeId , @Role = Role FROM #MYTEMP
END
