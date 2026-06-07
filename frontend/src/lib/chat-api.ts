const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

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
  updated_at: string
}

type ChatMessageResponse = {
  message_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

type ChatDetailResponse = {
  messages: ChatMessageResponse[]
}

type SendPromptResponse = {
  chat_id: string
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
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
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  return response.json() as Promise<TResponse>
}

export async function getChats(signal?: AbortSignal): Promise<ChatSummary[]> {
  const chats = await getJson<ChatSummaryResponse[]>('/chats', signal)

  return chats
    .map((chat) => ({
      id: chat.chat_id,
      title: chat.title,
      updatedAt: chat.updated_at,
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
  const chat = await getJson<ChatDetailResponse>(
    `/chats/${encodeURIComponent(chatId)}`,
    signal,
  )

  return chat.messages
    .map((message) => ({
      id: message.message_id,
      role: message.role,
      content: message.content,
      createdAt: message.created_at,
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
  const path = chatId ? `/chats/${encodeURIComponent(chatId)}` : '/chats'
  const response = await postJson<SendPromptResponse, { prompt: string }>(
    path,
    {
      prompt,
    },
  )

  return response.chat_id
}
