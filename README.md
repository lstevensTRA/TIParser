# TIParser

This project is a modern React (TypeScript, Tailwind) frontend for tax transcript parsing, analysis, and client management. It connects to a separately hosted FastAPI backend via API endpoints.

## Project Structure

```
TIParser/
  frontend/                # All React app code
    src/
      components/
      pages/
      services/
      types/
      ...
    .env                   # API base URL and other env vars
    package.json
    ...
  archive/                 # (Optional) For old scripts, reference code, etc.
  README.md
```

## Running the Frontend

1. **Install dependencies:**
   ```sh
   cd frontend
   npm install
   # or
   yarn install
   ```
2. **Set API base URL:**
   - Create a `.env` file in `frontend/` with:
     ```
     VITE_API_BASE=https://tiparser.onrender.com
     ```
3. **Start the dev server:**
   ```sh
   npm run dev
   # or
   yarn dev
   ```

## API Integration
- All API calls are managed in `frontend/src/services/`.
- TypeScript types for API responses/requests are in `frontend/src/types/`.
- The API base URL is set via `.env` as `VITE_API_BASE`.

## Keeping API Types in Sync

If your backend exposes an OpenAPI schema (e.g., FastAPI at `/openapi.json`):

1. **Install openapi-typescript:**
   ```sh
   npm install --save-dev openapi-typescript
   ```
2. **Add a script to `package.json`:**
   ```json
   "scripts": {
     "generate:api-types": "openapi-typescript https://tiparser.onrender.com/openapi.json --output src/types/openapi.d.ts"
   }
   ```
3. **Run the script:**
   ```sh
   npm run generate:api-types
   ```

## Contributing
- All new code should be placed in the `frontend/` directory.
- Use TypeScript and React best practices.
- Keep API types up to date with backend changes.

## Legacy/Reference Code
- Old scripts, Python files, and backend code are in the `archive/` directory for reference only.

---

For any questions or to update the backend API, coordinate with the backend team and update the frontend types as needed.
