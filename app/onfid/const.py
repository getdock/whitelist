CHECK_IN_PROGRESS = 'in_progress'
CHECK_AWAITING_APPLICANT = 'awaiting_applicant'
CHECK_COMPLETE = 'complete'
CHECK_WITHDRAWN = 'withdrawn'
CHECK_PAUSED = 'paused'
CHECK_REOPENED = 'reopened'

REPORT_AWAITING_DATA = 'awaiting_data'
REPORT_AWAITING_APPROVAL = 'awaiting_approval'
REPORT_COMPLETE = 'complete'
REPORT_WITHDRAWN = 'withdrawn'
REPORT_PAUSED = 'paused'
REPORT_CANCELLED = 'cancelled'

# If the report has returned information that needs to be evaluated, the overall result will be consider.
# If some of the reports contained in the check have either consider or unidentified as their results.
RESULT_CONSIDER = 'consider'

RESULT_CLEAR = 'clear'  #: If all the reports contained in the check have clear as their results.

# Identity report (standard variant) only - this is returned if the applicant fails an identity check. This indicates
#  there is no identity match for this applicant on any of the databases searched.
RESULT_UNIDENTIFIED = 'unidentified'

# Subresults

SUBRESULT_CLEAR = 'clear'  #: If all underlying verifications pass, the overall sub result will be clear

# If the report has returned information where the check cannot be processed further (poor quality image or an
# unsupported document).
SUBRESULT_REJECTED = 'rejected'

SUBRESULT_SUSPECTED = 'suspected'  #: If the document that is analysed is suspected to be fraudulent.

# If any other underlying verifications fail but they don’t necessarily point to a fraudulent document (such as the
# name provided by the applicant doesn’t match the one on the document)
SUBRESULT_CAUTION = 'caution'
