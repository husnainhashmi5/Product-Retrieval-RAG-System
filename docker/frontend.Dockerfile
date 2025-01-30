FROM node:20-alpine AS build

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

WORKDIR /app/frontend/rag-chat-frontend

COPY frontend/rag-chat-frontend/package*.json ./
RUN npm ci

COPY frontend/rag-chat-frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/frontend/rag-chat-frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
