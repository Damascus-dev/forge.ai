FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --only=production

COPY frontend/ ./
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
