# VideoGen Studio MCP Server

The MCP server runs inside the same `uvicorn` process as the rest of VideoGen Studio.

## Tools

| Tool                     | Description                                      |
| ------------------------ | ------------------------------------------------ |
| `videogen.speak`         | Speak text in a voice profile                    |
| `videogen.transcribe`    | Whisper transcription of audio                   |
| `videogen.list_captures` | Recent captures with transcripts                 |
| `videogen.list_profiles` | Available voice profiles                         |

## Usage

```json
{
  "mcpServers": {
    "videogen": {
      "url": "http://127.0.0.1:17493/mcp",
      "headers": { "X-Videogen-Client-Id": "claude-code" }
    }
  }
}
```
