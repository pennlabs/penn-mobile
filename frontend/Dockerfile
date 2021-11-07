FROM node:14-buster-slim

LABEL maintainer="Penn Labs"

WORKDIR /app/

# Copy project dependencies
COPY package.json /app/
COPY yarn.lock /app/

# Install project dependencies
RUN yarn install --frozen-lockfile --production=true

# Copy project files
COPY . /app/

# Disable telemetry back to zeit
ENV NEXT_TELEMETRY_DISABLED=1

# Build project
RUN yarn build

CMD ["yarn", "start"]
