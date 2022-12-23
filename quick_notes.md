## django authentication

```python
from django.contrib.auth.models import User
user = User.objects.create_user('myusername', 'myemail@crazymail.com', 'mypassword')
user.save()
```

