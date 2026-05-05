#!/usr/bin/env python3
"""Generate embeddings for all products without them."""
 
import asyncio
import sys
from dotenv import load_dotenv
 
load_dotenv()
 
from src.db.engine import engine, get_db
from src.db.models import Product
from src.services.embedding import get_embedding
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
 
 
async def generate_embeddings():
    """Generate embeddings for all products without them."""
    async with AsyncSession(engine) as session:
        # Get products without embeddings
        stmt = select(Product).where(Product.embedding.is_(None)).limit(50)
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        if not products:
            print("✅ All products have embeddings!")
            return
        
        print(f"Generating embeddings for {len(products)} products...")
        
        for i, product in enumerate(products, 1):
            try:
                # Create embedding text from product data
                text = f"{product.title} {product.description or ''} {' '.join(product.tags or [])}"
                embedding = await get_embedding(text)
                
                # Update product with embedding
                stmt = update(Product).where(Product.id == product.id).values(embedding=embedding)
                await session.execute(stmt)
                
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(products)} ✓")
                
            except Exception as e:
                print(f"  ❌ Error for product {product.id}: {e}")
        
        await session.commit()
        print(f"✅ Generated embeddings for {len(products)} products!")
 
 
if __name__ == "__main__":
    asyncio.run(generate_embeddings())
 