alter proc dbo.GetEmployeesForSkill @skillset varchar(2000), @AvailableInDays smallint
as 
begin 

	declare @url nvarchar(4000) = N'https://vema-ai-foundry.cognitiveservices.azure.com/openai/deployments/embedding-small/embeddings?api-version=2023-05-15';
	--declare @message nvarchar(max) = 'Backend developer skilled in Dotnet and CSharp';
	declare @payload nvarchar(max) = N'{"input": "' + @skillset + '"}';
	declare @query_embedding vector(1536)
	declare @ret int, @response nvarchar(max);
	SET @payload = N'{
		"input": "' + @skillset + '",
		"dimensions": 1536
		}'
	exec @ret = sp_invoke_external_rest_endpoint 
		@url = @url,
		@method = 'POST',
		@payload = @payload,
		@credential = [https://vema-ai-foundry.cognitiveservices.azure.com/],
		@timeout = 230,
		@response = @response output;

	set @query_embedding = CAST( json_query(@response, '$.result.data[0].embedding')  as VECTOR(1536));


	SELECT 
		t1.EmployeeId, 
		t2.EmployeeName, 
		Role, 
		Skills
		--,VECTOR_DISTANCE('cosine', @query_embedding, SkillsEmbedding) AS SkillsDistance
		--,VECTOR_DISTANCE('cosine', @query_embedding, RoleEmbedding) AS RoleDistance
	FROM EmployeeSkillsTest2 t1 
	join dbo.EmployeeDetails t2 
	on t1.EmployeeId = t2.EmployeeId
	join dbo.EmployeeProjectDetails t3
	on t1.EmployeeId = t3.EmployeeId 
	where t3.Status = 'Assigned'
	and DATEDIFF(DAY, GETDATE(), t3.EndDate) <= @AvailableInDays
	and 
		(VECTOR_DISTANCE('cosine', @query_embedding, SkillsEmbedding) <= 0.5
		OR  VECTOR_DISTANCE('cosine', @query_embedding, RoleEmbedding) <= 0.5)
	ORDER BY 
		VECTOR_DISTANCE('cosine', @query_embedding, SkillsEmbedding) +
		VECTOR_DISTANCE('cosine', @query_embedding, RoleEmbedding) ASC;
end

