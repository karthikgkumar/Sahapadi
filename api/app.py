import io
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Type
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
import openai
from dotenv import load_dotenv
import base64
from typing import List, Optional,Type, Tuple
from fastapi import FastAPI

from fastapi.responses import RedirectResponse, Response
from io import BytesIO
from pydantic import BaseModel
import openai
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import os
load_dotenv()  # This loads the variables from .env
from fastapi.responses import StreamingResponse
from mangum import Mangum
from io import BytesIO
load_dotenv() 


app=FastAPI()
handler=Mangum(app)


class PresentationRequest(BaseModel):
    topic: str
    num_slides: int
    theme: Optional[str] = "light"

class PresentationCreator:
    def _generate_content(self, topic: str, slide_number: int, total_slides: int) -> tuple:
        openaiclient = openai.Client(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_BASE_URL'),
    )
        
        syss = """
            You are a helpful assistant that can create creative presentation slides or PDFs on various topics. The user may ask you to create a presentation on a specific topic, and you should use the 'create_presentation' tool to generate the slides or PDF.

            To create a presentation, use the 'create_presentation' tool with the following arguments:
            - 'topic': The main topic of the presentation
            - 'format': Either 'slides' or 'pdf'
            - 'num_slides': Number of slides or pages to create (1-10)

            For example, if the user asks for a presentation about "Climate Change" with 5 slides, you should call the 'create_presentation' tool with the topic set to "Climate Change", format set to "slides", and num_slides set to 5.

            The content for each slide or page will be automatically generated based on the topic.

            Be sure to respond politely and let the user know if the presentation was created successfully or if there was an error. You can also offer to explain the content of the presentation or ask if they want any modifications.
            """

        prompt_n = f"""
        Create content for a presentation slide about {topic}.
        This is slide {slide_number} out of {total_slides}.
        Provide a title, three key points for the slide, and a prompt for generating an image related to the content.
        Format the output as:
        Title: [Your title here]
        - [First key point]
        - [Second key point]
        - [Third key point]
        Image prompt: [A descriptive prompt for generating an image related to the slide content]

        """
        msg = [
            {"role": "system", "content": syss},
            {"role": "user", "content": prompt_n},
        ]

        response = openaiclient.chat.completions.create(
            messages=msg,
            temperature=0.6,
            model="accounts/fireworks/models/firefunction-v2-rc",
            max_tokens=350,
            stream=False,
        )
        response = response.choices[0].message.content

        lines = response.strip().split('\n')
        title = lines[0].replace('Title: ', '')
        # content = '\n'.join(lines[1:-1])
        content_lines = lines[1:-1]
        formatted_content = []
        for line in content_lines:
            if line.strip():  # Check if the line is not empty
                formatted_line = f"• {line.strip().lstrip('-').strip()}"
                formatted_content.append(formatted_line)
    
        # Join content lines with null characters
        content = '\0'.join(formatted_content)
        image_prompt = lines[-1].replace('Image prompt: ', '')
        
        return title, content, image_prompt
    def _generate_image(self, prompt: str) -> BytesIO:
        image_api_url=os.getenv('IMAGE_API_URL')
        image_api_key=os.getenv('IMAGE_API_KEY')
        headers_image_api = {"Authorization": f"Bearer {image_api_key}"}
        data = {
            "model": "SG161222/Realistic_Vision_V3.0_VAE",
            "negative_prompt": "",
            "prompt": prompt,
            "width": 800,
            "height": 800,
            "steps": 33,
            "n": 1,
            "seed": 8000,
        }
        image_response = requests.post(
            image_api_url, json=data, headers=headers_image_api
        )
        image_response.raise_for_status()
        image_base64 = image_response.json()["output"]["choices"][0]["image_base64"]
        image_bytes = base64.b64decode(image_base64)
    
        return BytesIO(image_bytes)


    
    def _create_slides(self, topic: str, num_slides: int, theme: str) -> str:
        print(f"Creating slides presentation: topic='{topic}', num_slides={num_slides}, theme='{theme}'")
        prs = Presentation()
        
        # Define color schemes
        if theme.lower() == 'dark':
            background_color = RGBColor(32, 33, 36)  # Dark gray
            title_color = RGBColor(255, 255, 255)  # White
            subtitle_color = RGBColor(189, 193, 198)  # Light gray
            text_color = RGBColor(232, 234, 237)  # Off-white
        elif theme.lower() == 'professional':
            background_color = RGBColor(240, 240, 240)  # Light gray
            title_color = RGBColor(31, 73, 125)  # Dark blue
            subtitle_color = RGBColor(68, 114, 196)  # Medium blue
            text_color = RGBColor(0, 0, 0)  # Black
        elif theme.lower() == 'creative':
            background_color = RGBColor(255, 255, 255)  # White
            title_color = RGBColor(255, 67, 67)  # Coral red
            subtitle_color = RGBColor(255, 159, 28)  # Orange
            text_color = RGBColor(87, 117, 144)  # Steel blue
        elif theme.lower() == 'minimalist':
            background_color = RGBColor(255, 255, 255)  # White
            title_color = RGBColor(0, 0, 0)  # Black
            subtitle_color = RGBColor(128, 128, 128)  # Gray
            text_color = RGBColor(64, 64, 64)  # Dark gray
        elif theme.lower() == 'tech':
            background_color = RGBColor(18, 18, 18)  # Very dark gray
            title_color = RGBColor(0, 255, 255)  # Cyan
            subtitle_color = RGBColor(0, 204, 204)  # Darker cyan
            text_color = RGBColor(204, 204, 204)  # Light gray
        else:  # Default light theme
            background_color = RGBColor(255, 255, 255)  # White
            title_color = RGBColor(0, 82, 154)  # Dark blue
            subtitle_color = RGBColor(128, 128, 128)  # Gray
            text_color = RGBColor(64, 64, 64)  # Dark gray
        
        # Define slide layouts
        title_slide_layout = prs.slide_layouts[0]
        content_slide_layout = prs.slide_layouts[5]  # Blank layout
        
        # Create title slide
        title_slide = prs.slides.add_slide(title_slide_layout)
        title = title_slide.shapes.title
        subtitle = title_slide.placeholders[1]
        
        # Set background color
        background = title_slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = background_color
        
        title.text = topic.upper()
        subtitle.text = f"Generated by AvA"
        
        # Apply styling to title slide
        title.text_frame.paragraphs[0].font.size = Pt(50)
        title.text_frame.paragraphs[0].font.color.rgb = title_color
        subtitle.text_frame.paragraphs[0].font.size = Pt(32)
        subtitle.text_frame.paragraphs[0].font.color.rgb = subtitle_color
        
        for i in range(num_slides - 1):  # -1 because we already created the title slide
            slide = prs.slides.add_slide(content_slide_layout)
            title_slide_content = slide.shapes.title
            
            # Set background color
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = background_color
            
            title, content, image_prompt = self._generate_content(topic, i + 2, num_slides)
            
            title_slide_content.text = title
            # Apply styling to title
            title_slide_content.text_frame.paragraphs[0].font.size = Pt(50)
            title_slide_content.text_frame.paragraphs[0].font.color.rgb = title_color
            
            # Add content as a text box
            left = Inches(0.5)
            top = Inches(2)
            width = Inches(5)
            height = Inches(3)
            textbox = slide.shapes.add_textbox(left, top, width, height)
            text_frame = textbox.text_frame
            text_frame.word_wrap = True
            
            # Split content by null characters and add each line as a separate paragraph
            content_lines = content.split('\0')
            for idx, line in enumerate(content_lines):
                p = text_frame.add_paragraph()
                p.text = line+'\n'
                p.font.size = Pt(20)
                p.font.color.rgb = text_color
                p.alignment = PP_ALIGN.LEFT
            
            # Generate and add image
            image_stream = self._generate_image(image_prompt)
            left = Inches(5.5)
            top = Inches(2)
            width = Inches(4)
            height = Inches(5)
            slide.shapes.add_picture(image_stream, left, top, width=width, height=height)
        
        # Save the presentation to a BytesIO object
        pptx_file = BytesIO()
        prs.save(pptx_file)
        pptx_file.seek(0)
        
        return pptx_file


@app.post("/create_presentation")
async def create_presentation(request: PresentationRequest):
    creator = PresentationCreator()
    
    try:
        # Create the presentation in memory
        pptx_file = creator._create_slides(request.topic, request.num_slides, request.theme)
        
        # Return the file as a streaming response
        return StreamingResponse(
            pptx_file,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{request.topic.replace(" ", "_")}_presentation.pptx"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    




# Swagger UI is available at http://localhost:8000/docs
@app.get("/", response_class=RedirectResponse)
def redirect_to_docs():
    return "/docs"
# FastAPI app setup
app = FastAPI()

# Pydantic Models
class VisualAidArgs(BaseModel):
    content: str = Field(description="The content to be transformed into a visual aid")
    title: str = Field(description="Title of the document")
    aid_type: str = Field(
        description="Type of visual aid to generate",
        enum=["pdf", "roadmap", "ppt"],
        default="pdf"
    )

class VisualAidTool(BaseTool):
    name: str = "generate_visual_aid"
    description: str = "Generates visual aids (PDF, Roadmap, or PowerPoint) from given content"
    args_schema: Optional[Type[BaseModel]] = VisualAidArgs
    return_direct: Optional[bool] = True

    def _structure_content(self, content: str, title: str) -> dict:
        """
        Transform content into a structured format suitable for various visual aids
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

        3. Output Format:
           - Provide a list of main sections
           - Include key points under each section
           - Suggest potential visual representations

        Original Content:
        {content}
        """

        try:
            # Use OpenAI to structure the content
            openaiclient = openai.Client(
                api_key=os.getenv('OPENAI_API_KEY'),  # Add your OpenAI API key here
                base_url="https://api.fireworks.ai/inference/v1"
            )
            
            response = openaiclient.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert content structurer for visual presentations."},
                    {"role": "user", "content": prompt}
                ],
                model="accounts/fireworks/models/firefunction-v2-rc",
                max_tokens=1500,
                temperature=0.7
            )
            
            structured_content = response.choices[0].message.content
            return {
                "raw_content": structured_content,
                "sections": self._parse_sections(structured_content)
            }
        
        except Exception as e:
            return {
                "raw_content": content,
                "sections": [{"title": "Main Topic", "points": [content]}]
            }

    def _parse_sections(self, content: str) -> list:
        """
        Parse the structured content into sections
        """
        try:
            sections = []
            current_section = None
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('**') and line.endswith('**'):
                    # New section
                    if current_section:
                        sections.append(current_section)
                    current_section = {
                        "title": line.strip('**'),
                        "points": []
                    }
                elif line and current_section is not None:
                    # Add point to current section
                    current_section['points'].append(line)
            
            if current_section:
                sections.append(current_section)
            
            return sections
        except Exception:
            return [{"title": "Main Content", "points": [content]}]

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
                alignment=TA_CENTER,
                spaceAfter=12,
            
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['BodyText'],
                fontSize=18,
                textColor=HexColor('#00529A'),
                alignment=TA_LEFT,
                spaceAfter=12,
            
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=12,
                textColor=HexColor('#404040'),
                alignment=TA_JUSTIFY,
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

    def _run(self, content: str, title: str, aid_type: str = "pdf") -> str:
        """
        Main method to generate visual aid
        """
        # Structure the content
        structured_content = self._structure_content(content, title)

        # Generate appropriate visual aid
        if aid_type == "pdf":
            return self._generate_pdf(structured_content, title)
        else:
            return "Invalid visual aid type. Choose 'pdf'."

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
