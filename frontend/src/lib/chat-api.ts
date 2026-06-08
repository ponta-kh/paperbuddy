const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'
const USER_ID = import.meta.env.VITE_USER_ID

export type ChatSummary = {
  id: string
  title: string
  updatedAt: string
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
}

type ChatSummaryResponse = {
  chat_id: string
  title: string
  created_at: string
  last_updated_at: string
}

type ChatMessageResponse = {
  turn_id: string
  sender: 'user' | 'llm'
  content: string
  sent_at: string
}

type ListChatsResponse = {
  chats: ChatSummaryResponse[]
}

type ListChatMessagesResponse = {
  chat_id: string
  messages: ChatMessageResponse[]
}

type SendPromptResponse = {
  chat_id: string
  answer: string
  title: string
}

function getHeaders(includeContentType = false): Record<string, string> {
  if (!USER_ID) {
    throw new Error('VITE_USER_ID is not configured')
  }

  return {
    Accept: 'application/json',
    'X-User-ID': USER_ID,
    ...(includeContentType ? { 'Content-Type': 'application/json' } : {}),
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'GET',
    headers: getHeaders(),
    signal,
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  return response.json() as Promise<T>
}

async function postJson<TResponse, TBody>(
  path: string,
  body: TBody,
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: getHeaders(true),
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  return response.json() as Promise<TResponse>
}

export async function getChats(signal?: AbortSignal): Promise<ChatSummary[]> {
  const response = await getJson<ListChatsResponse>('/chats', signal)

  return response.chats
    .map((chat) => ({
      id: chat.chat_id,
      title: chat.title,
      updatedAt: chat.last_updated_at,
    }))
    .sort(
      (first, second) =>
        new Date(second.updatedAt).getTime() -
        new Date(first.updatedAt).getTime(),
    )
}

export async function getChatMessages(
  chatId: string,
  signal?: AbortSignal,
): Promise<ChatMessage[]> {
  const chat = await getJson<ListChatMessagesResponse>(
    `/chats/${encodeURIComponent(chatId)}/messages`,
    signal,
  )

  return chat.messages
    .map<ChatMessage>((message) => ({
      id: `${message.turn_id}:${message.sender}`,
      role: message.sender === 'user' ? 'user' : 'assistant',
      content: message.content,
      createdAt: message.sent_at,
    }))
    .sort(
      (first, second) =>
        new Date(first.createdAt).getTime() -
        new Date(second.createdAt).getTime(),
    )
}

export async function sendPrompt(
  prompt: string,
  chatId?: string,
): Promise<string> {
  const path = chatId
    ? `/chats/${encodeURIComponent(chatId)}/messages`
    : '/chats'
  const response = await postJson<SendPromptResponse, { prompt: string }>(
    path,
    {
      prompt,
    },
  )

  return response.chat_id
}
