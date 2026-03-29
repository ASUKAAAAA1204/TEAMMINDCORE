import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(function (_a) {
    var command = _a.command;
    return ({
        base: command === "build" ? "./" : "/",
        plugins: [react()],
        server: {
            host: "0.0.0.0",
            port: 4173,
            proxy: {
                "/health": "http://localhost:8000",
                "/tools": "http://localhost:8000",
                "/ingestion": "http://localhost:8000",
                "/retrieval": "http://localhost:8000",
                "/report": "http://localhost:8000",
                "/analysis": "http://localhost:8000",
                "/integration": "http://localhost:8000",
                "/installer": "http://localhost:8000",
                "/orchestrator": "http://localhost:8000",
            },
        },
    });
});
