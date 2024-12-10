import os
import io
import openai
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, Type
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
class VisualAidArgs(BaseModel):
    content: str = Field(description="The content to be transformed into a visual aid")
    title: str = Field(description="Title of the document", default="Content")
    aid_type: str = Field(
        description="Type of visual aid to generate",
        enum=["pdf", "roadmap", "ppt"],
        default="pdf"
    )

class VisualAidTool:
    def _enhance_educational_content(self, content: str, title: str) -> str:
        """
        Use AI to enhance and structure educational content
        """
        try:
            openaiclient = openai.Client(
                api_key=os.getenv('OPENAI_API_KEY'),  # Replace with actual API key
                base_url="https://api.fireworks.ai/inference/v1"
            )
            
            prompt = f"""Transform the following content about {content} into an enhanced, educational format:

            Transformation Guidelines:
            1. Educational Content Enrichment:
               - Break down complex concepts
               - Add explanatory context
               - Include relevant examples
               - Suggest learning connections

            2. Structure:
               - Create clear, logical sections
               - Use pedagogical approaches
               - Highlight key learning points

            Original Content:
            {content}
            """
            
            response = openaiclient.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert educational content enhancer."},
                    {"role": "user", "content": prompt}
                ],
                model="accounts/fireworks/models/firefunction-v2-rc",
                max_tokens=1500,
                temperature=0.7
            )
            
            enhanced_content = response.choices[0].message.content
            return enhanced_content
        
        except Exception as e:
            print(f"Content enhancement error: {e}")
            return content

    def _generate_pdf(self, content: str, title: str) -> io.BytesIO:
        """
        Generate an educational PDF with enhanced formatting
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()

            # Custom educational styles
            title_style = ParagraphStyle(
                'EducationalTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=HexColor('#003366'),
                alignment=TA_CENTER,
                spaceAfter=16,
            )
            
            section_style = ParagraphStyle(
                'EducationalSection',
                parent=styles['Heading2'],
                fontSize=18,
                textColor=HexColor('#005580'),
                alignment=TA_LEFT,
                spaceAfter=12,
            )
            
            body_style = ParagraphStyle(
                'EducationalBody',
                parent=styles['BodyText'],
                fontSize=12,
                textColor=HexColor('#333333'),
                alignment=TA_JUSTIFY,
                spaceAfter=10,
                leading=14
            )

            # Build story with educational elements
            story = []
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))

            # Process enhanced content
            enhanced_content = self._enhance_educational_content(content, title)
            
            # Split into sections and paragraphs
            sections = enhanced_content.split('\n\n')
            for section in sections:
                # Detect section headers
                if section.startswith('**') and section.endswith('**'):
                    section_title = section.strip('*')
                    story.append(Paragraph(section_title, section_style))
                else:
                    story.append(Paragraph(section, body_style))
                story.append(Spacer(1, 6))

            # Build PDF
            doc.build(story)
            buffer.seek(0)
            return buffer
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF Generation Error: {str(e)}")

# FastAPI Setup
app = FastAPI()

@app.post("/generate-pdf/")
async def generate_educational_pdf(visual_aid_args: VisualAidArgs):
    tool = VisualAidTool()

    try:
        pdf_buffer = tool._generate_pdf(visual_aid_args.content, visual_aid_args.title)

        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename={visual_aid_args.title.replace(' ', '_')}_educational_document.pdf"
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/", response_class=RedirectResponse)
def redirect_to_docs():
    return "/docs"
