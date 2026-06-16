from app.tools.email_tool import read_unread_emails, mark_as_read
from app.services.crew import process_email


def lambda_handler(event, context):
    try:
        emails = read_unread_emails()

        if not emails:
            print("No new emails found.")
            return {
                "statusCode": 200,
                "message": "No new emails to process",
                "emails_processed": 0
            }

        results = []
        for email_data in emails:
            try:
                result = process_email(email_data)
                results.append(result)
                
                # CRITICAL: Mark as read after processing!
                mark_as_read(email_data["id"])
                
            except Exception as e:
                print(f"Error processing email: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "sender": email_data.get("sender", "unknown")
                })

        success_count = sum(
            1 for r in results
            if r.get("overall_success") or r.get("success")
        )

        return {
            "statusCode": 200,
            "message": "Processing complete",
            "emails_processed": len(results),
            "successful": success_count,
            "failed": len(results) - success_count,
            "results": results
        }

    except Exception as e:
        print(f"Critical error in lambda_handler: {e}")
        return {
            "statusCode": 500,
            "message": "Lambda execution failed",
            "error": str(e)
        }