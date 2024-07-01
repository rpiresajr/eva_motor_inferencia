
functions = [
    {
    "type": "function",
    "function": {
      "name": "SearchEmailMessages",
      "description": "Search gmail messages using the gmail api",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "a custom gmail query"
          },
          "max_results": {
            "type": "string",
            "description": "number of quantity of results to return"
            
          }
        }
      },
      "required": ["query"],
    }
    },
    {
	 "type": "function",
	 "function": {
		"name": "GetMessage",
		"description": "Get information about an gmail message",
		"parameters": {
			"type": "object",
			 "properties": {
				"msg_id": {
					"type": "string",
					"description": "the id og the message"
				}
			 }
		},
		"required": ["msg_id"],
	 }
	},
    {
	 "type": "function",
	 "function": {
		"name": "SendMessage",
		"description": "Sends a message",
		"parameters": {
			"type": "object",
			 "properties": {
				"sender": {
					"type": "string",
					"description": "email of the sender of the message"
				},
				"to": {
					"type": "string",
					"description": "email of receiver of the message"
					
				},
                "subject": {
					"type": "string",
					"description": "subject of the message"
					
				},
                "message": {
					"type": "string",
					"description": "text of the message"
					
				}
			 }
		},
		"required": ["sender", "to", "subject", "message"],
	 }
	},
  {
  "type": "function",
  "function": {
  "name": "DeleteMessage",
  "description": "Deletes an message from gmail",
  "parameters": {
    "type": "object",
      "properties": {
      "msg_id": {
        "type": "string",
        "description": "id of the message"
      }
      }
  },
  "required": ["msg_id"],
  }
}
]