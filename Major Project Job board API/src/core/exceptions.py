from fastapi import HTTPException, status

# Base exception for when a requested resource (like an Application or Listing) is not found.
class ResourceNotFoundException(HTTPException):
    def __init__(self, resource_name: str, resource_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} with ID {resource_id} not found."
        )
        
class CompanyNotFound(ResourceNotFoundException):
    def __init__(self, company_id: int):
        super().__init__("Company", company_id)

# Exception for forbidden actions (403).  
class AuthorizationError(HTTPException):
    def __init__(self, detail: str = "Not authorized to perform this action."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class ApplicationNotFound(ResourceNotFoundException):
    def __init__(self, application_id: int):
        super().__init__("Application", application_id)
        
class ListingNotFound(ResourceNotFoundException):
    def __init__(self, listing_id: int):
        super().__init__("Job listing", listing_id)
 
# Base exception for when an authenticated user lacks the required profile."
class ProfileNotFoundException(HTTPException):
    def __init__(self, status_code: int = 404, detail: str = "Profile not found"):
        super().__init__(status_code=status_code, detail=detail)

class JobSeekerProfileNotFound(HTTPException):
    def __init__(self, seeker_id: int):
        # Pass the message to the parent HTTPException constructor
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Seeker Profile with ID {seeker_id} not found."
        )
        
class RecruiterProfileNotFound(ProfileNotFoundException):
    def __init__(self, recruiter_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recruiter profile with ID {recruiter_id} not found."
        )