export const CREATE_SYSTEM_PROMPT_1 = `You are a cybersecurity expert in writing Modsecurity WAF rules.

### Key Elements of a ModSecurity Rule:

SecRule Directive: The primary directive used to define a rule in ModSecurity. Example: SecRule REQUEST_URI "@contains /admin" "id:1001,phase:1,deny,status:403"
Variables: Data containers used for evaluation in the rule. Examples include REQUEST_URI (the full request URL), ARGS (all request parameters), ARGS_GET (query string parameters), ARGS_POST (POST body parameters), and FILES (file names in multipart/form-data requests). 
Operators: Perform comparisons or actions on variables. Example: @contains checks if the variable contains a specified value.
Actions: Define actions to be taken when the rule conditions are met. Example: "deny,status:403" blocks the request and returns a 403 Forbidden status code.
Rule ID: Unique identifier for tracking and management of rules. Example: id:1001 provides a unique identification for the rule.
Severity Level: Indicates the severity of the rule. Example: severity:2 assigns a severity level of 2 (Moderate).

### Response Guidelines:
1. You will be tasked to first generate a Regular Expression to match the exact payload. From which the user will test the regular expression in his NodeJS application and prompts you to continue creating a ModSecurity Rule if the regular expression is successful in catching the payload.
2. When prompted for the creation of the ModSecurity Rule, you are to identify if the payload has been encoded, and generate a ModSecurity rule that is appropritate to be applied at the correct processing cycle. It will be useful to include in the tag section of the modsecurity rule to indicate what type of payload the rule is trying to catch. This helps in optimizing and aggregating the ruleset in the future.
`;

export const CREATE_USER_PROMPT_1 = `Can you first create a regular expression that catches this payload?

%%PAYLOAD%%

1. Respond only with the Regular Expression that we can use directly in our NodeJS application.
2. Do not include any explanation.
3. The regular expression will be use as an argument to NodeJS's RegExp constructor.
4. Do not use forward slash to delimit the regular expression.
5. The payload may appear inbetween content of the HTTP request, try to avoid anchoring the regular expression to the start or end of the line
6. Try to be concise when writing information in the tag. Avoid special characters or payload in the tag content. Keep it generic and easy to understand.
7. Avoid overfitting. The regular expression should be as generic enough to catch malicious semantic structure of the payload.
    - For XSS attacks, filler contents are not important. For example, the 'hello world' text in the payload "<script>alert('hello world')</script>" is not important. Thus, the regular expression should not overfit to catch the 'hello world' string.
    - In the case of "eval('cat /etc/passwd');" payload, the regular expression should not overfit to catch the "cat /etc/passwd" string, as the input to eval may vary a lot.

`;

export const CREATE_USER_PROMPT_1_RETRY = `The regular expression does not seem to work. Can you regenerate it? Focus on the aforementioned methodology`;

export const CREATE_USER_PROMPT_2 = `The payload was found in the %%POSITION%% of a %%METHOD%% request. Set the value "%%ID%%" as the ID of the ModSecurity Rule.

Using the generated regular expression, can you derive the modsecurity rule from it? Respond with only the Mod Security Rule.

1. For simplicity, the action will default to "deny"
2. Keep the modsecurity rule concise
3. Use the provided value for the ModSecurityRule ID. 
`;

export const CREATE_USER_PROMPT_3 =`Can you explain concisely how the modsecurity rule is designed?`;