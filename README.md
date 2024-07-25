# Repo-to-Prompt API

This API allows you to process GitHub repositories and zip files, converting their contents into a formatted text output suitable for use as a prompt or context for language models.

## Features

- Process public GitHub repositories
- Process private GitHub repositories (with user-provided token)
- Process locally uploaded zip files
- Respect `.gitignore` patterns
- File size limit for zip uploads (50 MB) - this is how the demo is running. You can modify your version though. 

## API Endpoints

### POST /process_repo

This endpoint handles all three modes of operation:

1. Process a public GitHub repository
2. Process a private GitHub repository (requires user token)
3. Process an uploaded zip file

#### Request Format

For GitHub repositories (public or private):

```json
{
    "repo_url": "https://github.com/username/repo",
    "token": "your_github_token"  // Optional, required for private repos
}
```

For zip file uploads:

- Use `multipart/form-data` with a file field named `file`
- The file must be a zip archive

#### Response Format

Success response:

```json
{
    "result": "formatted_output_text"
}
```

Error response:

```json
{
    "error": "error_message"
}
```

## Try it out

You can try the API using curl below. Keep in mind that Render instance has a cold start and may take up to 50 seconds to spin up.

```bash
curl --location 'https://repo-to-prompt.onrender.com/process_repo' \
--header 'Content-Type: application/json' \
--data '{
    "repo_url": "https://github.com/elisha-rudenkov/repo-to-prompt"
}'
```

## Local Version

A local version of the script is available that works directly with zip files. To use it:

1. Save gpt-generator.py

2. Run the script:

```bash
python gpt-generator.py
```

3. Enter the path to your zipped GitHub repo when prompted, or press Enter to use the first zip file in the current directory.

4. The script will process the zip file and create a `gpt-context.txt` file with the formatted output.

## Error Handling

The API includes error handling for various scenarios, such as:

- Invalid or missing repository URL
- File size exceeding the limit for zip uploads
- GitHub API errors
- File reading errors

In case of an error, the API will return an appropriate error message in the response.

## Security Considerations

- The API uses `secure_filename` to sanitize uploaded file names.
- A file size limit is enforced for zip uploads to prevent abuse.
- User-provided GitHub tokens are not stored and are only used for the duration of the request.

## Limitations

- The API currently only supports GitHub repositories and zip files.
- Large repositories or zip files may take longer to process.
- Binary files are not included in the output.
