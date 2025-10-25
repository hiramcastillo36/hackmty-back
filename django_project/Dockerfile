FROM python:3.10-alpine3.20
LABEL maintainer="Hiram Castillo - hcastillo@ixmatix.com"

ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt /tmp/requirements.txt
WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt 2>/dev/null || true; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

ENV PATH="/py/bin:$PATH"

# Copy project files (do this after pip install to leverage Docker cache)
COPY . /app/

# Change ownership to django-user
RUN chown -R django-user:django-user /app

USER django-user

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
