JSON
====

Flask-Security provide you with a few very useful views out-of-the-box. As seen in !!link to customizing views!!, 
they're quite customizable. Besides that, they're also capable of handing out proper json responses given
your request mimetype is **application/json** as explained in Flask's official documentation. 

The following views support JSON response (ajax friendly):

login
  handles user authentication; just drop the authentication_token if you
  don't need stateless API behavior;
  should be called with **POST**
  
  **request body**
  
  * email
  * password
  * remember
  * csrf_token
  
  **response body**
  
  dict(
    meta=dict(code=int), 
    response=dict(
      user=dict(
        id=int, 
        authentication_token=str
      )))
logout
  handles user session invalidation; should be called with **POST** (doesn't quite support JSON response yet)
register
  registers a new user; should be called with **POST**
forgot_password
  requests a password reset; should be called with **POST**
change_password
  handles password reset; should be called with **POST**
