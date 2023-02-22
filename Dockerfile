FROM python:3.9
ENV PYTHONUNBUFFERED 1
EXPOSE 8000
RUN mkdir /backend
WORKDIR /backend
COPY ./requirements.txt /backend/
RUN pip install --no-cache-dir -r /backend/requirements.txt
COPY . /backend/
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
