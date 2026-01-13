# About repo
This is a hobby repository for a webpage under the domain 'xavier.now'. The goal of this page is to showcase blog posts that xavier posts as well as provide information about xavier as an engineer. The goal of this project is to have a page that behaves similarly to google docs. There is one user, the admin user that has the ability to edit blog posts. Every other user can view these changes real time, just like google docs. They are unable to edit them, only view, as well as view older blog posts which are no longer open to editing. 

# About file
This file serves as a small software design document for claude. This isn't set in stone, but rather serves as a guiding tool for the domain of the project. 

## Narrative 
On any given day, Xavier logins to xavier.now and is then shown the post of the day. This looks like a document ready for editing in google docs. Xavier writes whatever he wishes to write and spends time editing this post. At the same time, other users on the page can see Xavier editing the post live. Though they're unable to do changes themselves, they are real time viewers of xavier's actions. Once xavier is done, he is able to publish this post which will be saved. Users are able to then check for previous posts and see this post as well as previous others. Posts are organized by date and every post corresponds to the date Xavier edited them. The post is only available for changes on their corresponding day (i.e. the post on 1/1/2026 will close for editing on 1/2/2026). Posts that are closed are immediately published. 

## Functional requirements
- Admin should be able to edit the current post
- Admin should be able to save posts
- Admin should be able to see a number count of people connected
- Users should be able to view admin changes real time
- Users should be able to see admin's cursor on the document
- Users should be able to view admin's previous posts
- Users should be able to view information about admin (about page)

## Nonfunctional requirements
- The system should have a login for only the admin
- The system should have real time response time to changes made in the current document (sub 1 second)
- The system should allow many readers at once (10,000 concurrently)
- THe system should allow only one login for admin; never more, and only one user (xavier) will ever be admin
- The system should track amount of live readers
- The system should be ready to spawn a new post anytime xavier logins for the day if it doesn't already exist
- The system should close an open post once the day is over

## Core entities
- User
- Admin
- Post
  - Content: string
  - Status: Open | Closed
  - Date: datetime

## API rough sketch
```
//Returns todays post (maybe redirect)
- GET / -> Post
//Separate static webpage that showcases information about Xavier
- GET /about -> AboutMe
//Shows the archive/list of previous posts 
- GET /posts -> List[Post]
//For xavier to login as admin and be able to edit todays posts
- POST /login -> RedirectAdmin
{
	username: string
	passwd: safe password
	device_ip: string
}
```

## Coding style
Code in this repository should be using modern idiomatic python. Components can and should be done with javascript to support the functionality of the frontend. Avoid large and unnecessary commments. Prioritize clean and modular code. Performance and security is important.

## Technology stack
- Python 
- FastAPI, websockets
- Jinja templates (possibly)
- Javascript
