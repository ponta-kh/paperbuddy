import "@aws-amplify/ui-react/styles.css";
import { Authenticator } from "@aws-amplify/ui-react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import ChatPage from "./features/chat/ChatPage.tsx";
import { SystemErrorPage } from "./features/system/SystemErrorPage.tsx";
import { configureAuth } from "./lib/auth.ts";

const rootElement = document.getElementById("root");

if (!rootElement) {
    throw new Error("Root element not found");
}

const root = createRoot(rootElement);

configureAuth()
    .then(() => {
        root.render(
            <StrictMode>
                <Authenticator loginMechanisms={["email"]}>
                    <ChatPage />
                </Authenticator>
            </StrictMode>,
        );
    })
    .catch(() => {
        root.render(<SystemErrorPage />);
    });
