# Chat API Documentation

Natural language device control endpoints for MobileDroid AI Agent.

## Endpoints

### Send Chat Command

**Endpoint:** `POST /chat/profiles/{profile_id}`

Send a natural language command to control an Android device.

**Parameters:**
- `profile_id` (string): The profile ID of the running Android device

**Request Body:**
```json
{
  "message": "Your natural language command",
  "max_steps": 20
}
```

**Fields:**
- `message` (string, required): Natural language instruction for the AI agent
- `max_steps` (integer, optional): Maximum automation steps before timeout (default: 20)

**Response:**
```json
{
  "success": true,
  "response": "Detailed description of what was accomplished",
  "steps_taken": 5,
  "error": null
}
```

**Response Fields:**
- `success` (boolean): Whether the task completed successfully
- `response` (string): AI's description of what it accomplished
- `steps_taken` (integer): Number of automation steps executed
- `error` (string|null): Error message if task failed

### Get Chat Examples

**Endpoint:** `GET /chat/examples`

Retrieve example commands organized by category.

**Response:**
```json
{
  "examples": [
    {
      "category": "Navigation",
      "commands": [
        "Open the settings app",
        "Go to the home screen",
        "Open the app drawer",
        "Go back to the previous screen"
      ]
    },
    {
      "category": "Interaction", 
      "commands": [
        "Click on the Search button",
        "Tap the menu icon",
        "Swipe up on the screen",
        "Long press on the app icon"
      ]
    }
  ]
}
```

## Usage Examples

### Simple Screenshot Analysis

**Request:**
```bash
curl -X POST http://34.235.77.142:8100/chat/profiles/019b998c-2b40-7a08-a50d-fc6591d3ab71 \
  -H "Content-Type: application/json" \
  -d '{"message": "What do you see on the screen?", "max_steps": 1}'
```

**Response:**
```json
{
  "success": true,
  "response": "I can see the Android home screen with a dark wallpaper. There are three app icons in the dock at the bottom: a contacts app, an Android app, and a camera app. The time shown in the status bar is 5:59.",
  "steps_taken": 1,
  "error": null
}
```

### App Navigation

**Request:**
```bash
curl -X POST http://34.235.77.142:8100/chat/profiles/019b998c-2b40-7a08-a50d-fc6591d3ab71 \
  -H "Content-Type: application/json" \
  -d '{"message": "Open the settings app", "max_steps": 5}'
```

**Response:**
```json
{
  "success": true,
  "response": "I successfully opened the Settings app. I can see the main settings menu with options like Network & internet, Connected devices, Apps, and Battery.",
  "steps_taken": 2,
  "error": null
}
```

### Complex Task

**Request:**
```bash
curl -X POST http://34.235.77.142:8100/chat/profiles/019b998c-2b40-7a08-a50d-fc6591d3ab71 \
  -H "Content-Type: application/json" \
  -d '{"message": "Turn on airplane mode", "max_steps": 10}'
```

**Response:**
```json
{
  "success": true,
  "response": "I successfully enabled airplane mode by opening Settings, navigating to Network & internet, and toggling the airplane mode switch to the on position.",
  "steps_taken": 4,
  "error": null
}
```

### Error Example

**Request:**
```bash
curl -X POST http://34.235.77.142:8100/chat/profiles/019b998c-2b40-7a08-a50d-fc6591d3ab71 \
  -H "Content-Type: application/json" \
  -d '{"message": "Install an app that does not exist", "max_steps": 10}'
```

**Response:**
```json
{
  "success": false,
  "response": "Task failed: Could not find the specified app in the Play Store after searching.",
  "steps_taken": 6,
  "error": "App not found in search results"
}
```

## Command Categories

### Navigation Commands
- `"Go to the home screen"`
- `"Open the app drawer"`
- `"Go back to the previous screen"`
- `"Open [app name]"`
- `"Switch to recent apps"`

### Interaction Commands
- `"Click on [element]"`
- `"Tap the [color] button"`
- `"Long press on [element]"`
- `"Swipe [direction]"`
- `"Scroll down/up"`

### Text Input Commands
- `"Type '[text]' in the text field"`
- `"Search for '[query]'"`
- `"Enter your email address"`
- `"Clear the text field"`

### Settings Commands
- `"Turn on/off [setting]"`
- `"Enable/disable [feature]"`
- `"Change [setting] to [value]"`
- `"Open [settings category]"`

### App-Specific Commands
- `"Send a message to [contact]"`
- `"Take a photo"`
- `"Set an alarm for [time]"`
- `"Call [contact]"`
- `"Play [music/video]"`

### Analysis Commands
- `"What do you see on the screen?"`
- `"What apps are visible?"`
- `"Read the notification"`
- `"What's the current time?"`
- `"Describe the layout"`

## Error Handling

### Common Error Types

**Profile Not Found (404)**
```json
{"detail": "Profile not found"}
```

**Profile Not Running (400)**
```json
{"detail": "Profile not running"}
```

**No LLM Configuration (500)**
```json
{"detail": "No chat integration configured. Please set up LLM provider configuration."}
```

**Agent Connection Error (500)**
```json
{
  "success": false,
  "response": "An error occurred while executing your command",
  "error": "Failed to connect to device"
}
```

### Retry Logic

The agent includes automatic retry logic for:
- Temporary UI detection failures
- Network connectivity issues
- Transient ADB connection problems

For persistent errors, the agent will fail gracefully with a descriptive error message.

## Performance Considerations

### Timing Expectations
- **Simple tasks** (1-2 steps): 10-30 seconds
- **Medium tasks** (3-5 steps): 30-90 seconds
- **Complex tasks** (5+ steps): 2-5 minutes

### Optimization Tips
- Be specific in commands ("tap the blue Submit button" vs "click something")
- Break complex workflows into smaller tasks
- Use lower `max_steps` for simple operations
- Consider device performance and app responsiveness

### Rate Limiting
- No explicit rate limits currently implemented
- Claude API has standard rate limits (60 requests/minute)
- Consider device processing time between requests

## Integration Examples

### JavaScript/Node.js

```javascript
const sendChatCommand = async (profileId, message, maxSteps = 20) => {
  const response = await fetch(`/chat/profiles/${profileId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      max_steps: maxSteps
    })
  });
  
  return await response.json();
};

// Usage
const result = await sendChatCommand(
  "019b998c-2b40-7a08-a50d-fc6591d3ab71", 
  "Open the calculator app"
);

console.log(result.success ? result.response : result.error);
```

### Python

```python
import requests

def send_chat_command(profile_id, message, max_steps=20):
    url = f"http://34.235.77.142:8100/chat/profiles/{profile_id}"
    payload = {
        "message": message,
        "max_steps": max_steps
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Usage
result = send_chat_command(
    "019b998c-2b40-7a08-a50d-fc6591d3ab71",
    "Turn on Wi-Fi"
)

if result["success"]:
    print(f"Success: {result['response']}")
    print(f"Steps taken: {result['steps_taken']}")
else:
    print(f"Failed: {result['error']}")
```

### cURL

```bash
# Simple command
curl -X POST http://34.235.77.142:8100/chat/profiles/PROFILE_ID \
  -H "Content-Type: application/json" \
  -d '{"message": "Take a screenshot", "max_steps": 1}'

# Complex command with timeout
curl -X POST http://34.235.77.142:8100/chat/profiles/PROFILE_ID \
  -H "Content-Type: application/json" \
  -d '{"message": "Install WhatsApp from Play Store", "max_steps": 15}' \
  --max-time 300
```

## Best Practices

### Command Writing
1. **Be specific**: "Tap the blue Submit button" vs "click the button"
2. **Use clear language**: Avoid ambiguous terms or slang  
3. **Break down complex tasks**: Separate multi-step workflows
4. **Include context**: Mention app names, screen locations, colors

### Error Recovery
1. **Check response**: Always verify `success` field before proceeding
2. **Handle timeouts**: Set appropriate `max_steps` for task complexity
3. **Retry logic**: Implement exponential backoff for transient failures
4. **Fallback options**: Have alternative approaches for critical workflows

### Performance
1. **Optimize steps**: Use lower `max_steps` for simple tasks
2. **Batch operations**: Group related commands when possible
3. **Monitor usage**: Track token consumption and response times
4. **Cache results**: Store successful command patterns for reuse

For more technical details, see the [Agent Architecture Documentation](../lib/agent/README.md).