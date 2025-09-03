import { NextResponse } from 'next/server';

// In Docker, we need to use the service name as the hostname
const API_URL = process.env.NODE_ENV === 'production' 
  ? 'http://backend:8000'
  : 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const { question } = await request.json();

    console.log('Sending request to:', `${API_URL}/generate`);

    const response = await fetch(`${API_URL}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', errorText);
      throw new Error(`Failed to fetch from backend: ${errorText}`);
    }

    const data = await response.json();
    
    // Transform the response to match our frontend's expected format
    return NextResponse.json({
      answer: data.answer,
      references: data.references.map((url: string) => ({
        page_url: url,
        page_title: url.split('/').pop() || url // Use the last part of URL as title
      })),
      scores: data.evaluation?.llm_evaluation?.scores || {
        factual_accuracy: 0,
        relevance: 0,
        completeness: 0,
        context_usage: 0
      }
    });
  } catch (error) {
    console.error('Error in chat API:', error);
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    );
  }
} 