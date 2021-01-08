from srna_api.providers.user_provider import UserProvider

user_provider = UserProvider()

#Returns true or false if the user is allowed to view student information
#Test developers are not allowed to see student information
def view_student_data(user):

    allow = True

    is_admin = user_provider.has_role(user, 'Administrator')
    is_instructor = user_provider.has_role(user, 'Instructor')
    is_test_developer = user_provider.has_role(user, 'Test Developer')

    if not is_admin:
        if not is_instructor:
            if is_test_developer:
                allow = False
    return allow

#Returns the following strings:
# "all" : to see all student classes
# "none" : none of the student classes
# "own" : user own's classes

def view_student_classes(user):
    is_admin = user_provider.has_role(user, 'Administrator')
    is_instructor = user_provider.has_role(user, 'Instructor')
    is_test_developer = user_provider.has_role(user, 'Test Developer')

    if is_admin:
       return 'all'

    if is_test_developer:
        return "all"

    if is_instructor:
        return "own"
