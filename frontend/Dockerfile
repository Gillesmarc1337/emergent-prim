FROM node:22-alpine

WORKDIR /app

# Install dependencies
COPY package.json ./
# Copy yarn.lock if it exists
COPY yarn.lock* ./
# Install dependencies (use npm if yarn fails)
RUN if [ -f yarn.lock ]; then yarn install --frozen-lockfile; else yarn install || npm install; fi

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start the development server
CMD ["yarn", "start"]

