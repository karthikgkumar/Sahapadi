import io
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Type
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from openai import Client

# FastAPI app setup
app = FastAPI()

# Tool List (same as the previous answer)
tools = [
    {
        "type": "function",
        "function": {
            'name': 'generate_visual_aid',
            'description': 'Generates visual aids such as PDFs, roadmaps, and presentations from given content.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'action': {
                        'type': 'string',
                        'enum': ['create_pdf', 'create_roadmap', 'create_presentation'],
                        'description': 'The action to perform: create_pdf, create_roadmap, or create_presentation.'
                    },
                    'content': {
                        'type': 'string',
                        'description': 'The content that needs to be transformed into a visual aid.'
                    },
                    'title': {
                        'type': 'string',
                        'description': 'The title of the document or visual aid.'
                    },
                    'aid_type': {
                        'type': 'string',
                        'enum': ['pdf', 'roadmap', 'ppt'],
                        'default': 'pdf',
                        'description': 'The type of visual aid to generate: pdf, roadmap, or ppt.'
                    }
                },
                'required': ['action', 'content', 'title']
            }
        }
    }
]

# Pydantic Models
class VisualAidArgs(BaseModel):
    content: str = Field(description="The content to be transformed into a visual aid")
    title: str = Field(description="Title of the document")
    aid_type: str = Field(
        description="Type of visual aid to generate",
        enum=["pdf", "roadmap", "ppt"],
        default="pdf"
    )

class VisualAidTool:
    name: str = "generate_visual_aid"
    description: str = "Generates visual aids (PDF, Roadmap, or PowerPoint) from given content"
    args_schema: Optional[Type[BaseModel]] = VisualAidArgs
    return_direct: Optional[bool] = True

    def _generate_pdf(self, structured_content: dict, title: str) -> io.BytesIO:
        """
        Generate PDF with advanced formatting and return it as a BytesIO stream
        """
        try:
            # Use BytesIO instead of saving to a file
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=HexColor('#00529A'),
                alignment=1,  # Centered
                spaceAfter=12,
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['BodyText'],
                fontSize=18,
                textColor=HexColor('#00529A'),
                alignment=0,  # Left aligned
                spaceAfter=12,
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=12,
                textColor=HexColor('#404040'),
                alignment=4,  # Justified
                spaceAfter=12,
            )

            # Build story
            story = []
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))

            # Add sections
            for section in structured_content['sections']:
                story.append(Paragraph(section['title'], heading_style))
                for point in section['points']:
                    story.append(Paragraph(point, body_style))
                story.append(Spacer(1, 6))

            # Build PDF
            doc.build(story)

            # Seek to the beginning of the BytesIO stream
            buffer.seek(0)
            return buffer
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating PDF: {str(e)}")

    def _structure_content(self, content: str, title: str) -> dict:
        """
        Transform content into a structured format suitable for visual aids
        """
        prompt = f"""Transform the following content about {title} into a structured, educational format:

        Transformation Guidelines:
        1. Create a clear document structure with:
           - Main sections and key points
           - Logical flow of information
           - Highlights of critical concepts

        2. Prepare content for visual representation:
           - Break down complex ideas
           - Create concise, impactful statements
           - Identify potential visual elements

        Original Content:
        {content}
        """

        # Here you should connect to OpenAI or your model to structure the content
        # For now, returning a mock structure
        return {
            "raw_content": content,
            "sections": [{"title": "Main Topic", "points": [content]}]
        }

    def _run(self, content: str, title: str, aid_type: str = "pdf") -> io.BytesIO:
        """
        Main method to generate visual aid
        """
        # Structure the content
        structured_content = self._structure_content(content, title)

        # Generate appropriate visual aid
        if aid_type == "pdf":
            return self._generate_pdf(structured_content, title)
        else:
            return None

# FastAPI endpoint for generating PDF
@app.post("/generate-pdf/")
async def generate_pdf(visual_aid_args: VisualAidArgs):
    tool = VisualAidTool()

    try:
        pdf_buffer = tool._run(visual_aid_args.content, visual_aid_args.title, visual_aid_args.aid_type)

        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename={visual_aid_args.title.replace(' ', '_')}_document.pdf"
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/", response_class=RedirectResponse)
def redirect_to_docs():
    return "/docs"
