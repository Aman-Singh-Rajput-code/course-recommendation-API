from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
import json
from dotenv import load_dotenv
from waitress import serve
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes (or set specific origins if needed)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize Gemini Pro 1.5
def initialize_gemini():
    # Get API key from environment variables
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY environment variable. Please check your .env file.")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    return model

def get_course_recommendations(subject, budget, skill_level, time_availability, learning_style):
    try:
        model = initialize_gemini()
        
        prompt = f"""
        Act as a course recommendation system. Provide course recommendations based on the following parameters:
        - Subject: {subject}
        - Budget: {budget}
        - Skill Level: {skill_level}
        - Time Availability: {time_availability}
        - Learning Style: {learning_style}

        ### **Instructions for Course URLs:**
        - Only recommend courses from real platforms like **Coursera, YouTube, GeeksForGeeks, Udemy, edX, LinkedIn Learning, Pluralsight, or Khan Academy**.
        - **DO NOT generate fake URLs.** Only provide real, verifiable course links.
        - If you are unsure about a course URL, mention **"URL not found"** instead of a fake link.

        Return your response in the following JSON format:
        {{
            "recommendations": [
                {{
                    "course_name": "Course name",
                    "platform": "Platform name",
                    "cost": "Cost in USD",
                    "duration": "Estimated completion time",
                    "description": "Brief description",
                    "url": "Real course link or 'URL not found'",
                    "skill_level": "Beginner/Intermediate/Advanced"
                }}
            ],
            "roadmap": [
                {{
                    "stage": "Stage 1: Fundamentals",
                    "description": "Description of this stage",
                    "estimated_time": "Time to complete this stage",
                    "key_skills": ["skill1", "skill2", "skill3"],
                    "resources": ["resource1", "resource2"]
                }}
            ],
            "additional_tips": "Additional learning tips"
        }}
        """
        
        print("Sending prompt to Gemini:", prompt)
        response = model.generate_content(prompt)
        print("Received response from Gemini")
        
        # Parse the response to get the JSON
        response_text = response.text
        print(f"Raw response: {response_text[:500]}...")  # Print first 500 chars for debugging
        
        # Extract JSON from the response if it's wrapped in code blocks
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].strip()
        else:
            json_str = response_text
        
        print(f"Extracted JSON string: {json_str[:500]}...")  # Print first 500 chars
        recommendations = json.loads(json_str)
        return recommendations
    except ValueError as ve:
        print(f"ValueError: {str(ve)}")
        # Handle API key errors
        if "API key" in str(ve):
            # Use fallback data for demo purposes when API key is missing
            return get_fallback_data(subject, skill_level)
        return {"error": str(ve)}
    except Exception as e:
        print(f"Error in get_course_recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        # Handle other exceptions
        return {"error": f"Error getting recommendations: {str(e)}"}

# Fallback function for testing when API is not working
def get_fallback_data(subject, skill_level):
    print("Using fallback data")
    return {
        "recommendations": [
            {
                "course_name": f"{subject} for {skill_level}s",
                "platform": "Coursera",
                "cost": "$49.99",
                "duration": "8 weeks",
                "description": f"A comprehensive introduction to {subject} designed for {skill_level.lower()} learners.",
                "url": "https://coursera.org",
                "skill_level": skill_level
            },
            {
                "course_name": f"Advanced {subject}",
                "platform": "Udemy",
                "cost": "$29.99",
                "duration": "10 weeks",
                "description": f"Take your {subject} skills to the next level with practical projects.",
                "url": "https://udemy.com",
                "skill_level": "Intermediate"
            },
            {
                "course_name": f"{subject} Bootcamp",
                "platform": "edX",
                "cost": "$199.99",
                "duration": "12 weeks",
                "description": f"Intensive {subject} training with industry experts.",
                "url": "https://edx.org",
                "skill_level": "Advanced"
            }
        ],
        "roadmap": [
            {
                "stage": "Stage 1: Fundamentals",
                "description": f"Learn the basic concepts and principles of {subject}",
                "estimated_time": "4 weeks",
                "key_skills": ["Basic concepts", "Terminology", "Simple applications"],
                "resources": ["Textbooks", "Online tutorials"]
            },
            {
                "stage": "Stage 2: Practical Application",
                "description": f"Apply your knowledge of {subject} to real-world problems",
                "estimated_time": "6 weeks",
                "key_skills": ["Problem-solving", "Tool usage", "Applied techniques"],
                "resources": ["Practice exercises", "Case studies"]
            },
            {
                "stage": "Stage 3: Advanced Topics",
                "description": f"Explore specialized areas within {subject}",
                "estimated_time": "8 weeks",
                "key_skills": ["Advanced methodologies", "Specialized tools", "Research skills"],
                "resources": ["Academic papers", "Expert workshops"]
            }
        ],
        "additional_tips": f"Consider joining online communities related to {subject} to network with other learners and professionals. Consistent practice is key to mastering this field."
    }

@app.route('/get_recommendations', methods=['POST'])
def recommendations():
    try:
        data = request.json
        print(f"Received data: {data}")  # Debug print
        
        subject = data.get('subject', '')
        budget = data.get('budget', '')
        skill_level = data.get('skillLevel', '')
        time_availability = data.get('timeAvailability', '')
        learning_style = data.get('learningStyle', '')
        
        if not subject:
            return jsonify({"error": "Subject is required"}), 400
        
        print(f"Calling Gemini API with params: {subject}, {budget}, {skill_level}, {time_availability}, {learning_style}")
        result = get_course_recommendations(subject, budget, skill_level, time_availability, learning_style)
        print(f"API response: {result}")  # Debug print
        return jsonify(result)
    except Exception as e:
        print(f"Error in recommendations route: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
       # Run the app locally using Waitress
    from os import environ
    port = int(environ.get("PORT", 5000))  # Default to port 5000
    serve(app, host='0.0.0.0', port=port)
   
''' PORT = int(os.getenv("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0", port=PORT)'''
