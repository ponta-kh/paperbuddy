import "@aws-amplify/ui-react/styles.css";
import { Authenticator } from "@aws-amplify/ui-react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import Chat from "./Chat.tsx";
import { SystemErrorScreen } from "./components/system/SystemErrorScreen.tsx";
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
                    <Chat />
                </Authenticator>
            </StrictMode>,
        );
    })
    .catch(() => {
        root.render(<SystemErrorScreen />);
    });
