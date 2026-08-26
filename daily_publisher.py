import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Chic Outfit Ideas for a Peaceful Countryside Escape",
        "Easy Everyday Elegance: A Capsule Wardrobe Guide",
        "The Beauty Routine That Makes Me Feel Confident",
        "5 Travel Essentials for Effortless Style on the Go",
        "How to Find Your Signature Everyday Look",
        "Soft Glam Makeup for an Elegant Evening Out",
        "A Slow Morning in the Countryside: My Routine",
        "Timeless Fashion Pieces Every Woman Should Own",
        "Travel Diary: Exploring Hidden Corners of the City",
        "Confidence Starts with How You Dress",
        "Creating Beautiful Moments in Ordinary Days",
        "The Art of Effortless Elegance",
        "My Favorite Cozy Knitwear for Autumn Days",
        "Beauty in the Little Things: A Day in My Life",
        "Pack Light, Look Chic: My Travel Wardrobe Tips",
    ]

    fallback_descriptions = [
        "Fashion is a way to tell the world who you are without saying a word. This countryside look is all about soft fabrics, neutral tones, and quiet confidence. Save this for your next getaway! 🌿 #fashion #style #countryside #outfitinspo #elegance #mirelle",
        "Beauty doesn't have to be complicated. A few mindful steps each morning help me feel put-together and calm. Try this gentle routine and notice the difference. Like if you're prioritizing self-care! 💄 #beauty #skincare #morningroutine #selfcare #mirelle",
        "Travel teaches us to see the world with fresh eyes. Light layers and comfortable shoes keep me stylish from morning markets to evening walks. Comment your favorite travel destination below! ✈️ #travel #travelstyle #explore #wanderlust #mirelle",
        "Effortless elegance is a choice, not a price tag. Mix timeless basics with one special piece and you're ready for anything. Share this with a friend who loves quiet luxury! ✨ #fashion #elegant #timeless #styleinspo #mirelle",
        "The little moments make life beautiful. A cup of tea by the window, soft light, a good book — these are the days I treasure. Double tap if you love slow living! ☕ #lifestyle #slowliving #cozy #everydaybeauty #mirelle",
        "Confidence is the best accessory you own. Wear what makes you feel like yourself and the rest follows. Drop a 🌸 if you're embracing your style! #confidence #style #selflove #fashion #mirelle",
        "A peaceful countryside escape resets my creativity. Rolling hills, fresh air, and simple outfits let me breathe. Save this for your next trip inspiration! 🌾 #countryside #travel #nature #escape #mirelle",
        "Timeless pieces never go out of style. A tailored coat, a silk scarf, and good shoes carry you through every season. Like if you love capsule wardrobes! 🧥 #fashion #timeless #wardrobe #elegance #mirelle",
        "Creativity lives in the everyday. I find inspiration in color, texture, and the way light falls in the afternoon. Comment what inspires you! 🎨 #creativity #inspiration #lifestyle #artofliving #mirelle",
        "Beauty is in the details. A glossy lip, a spritz of perfume, a moment to yourself — small rituals, big joy. Follow Mirelle for daily beauty and lifestyle inspiration! 💐 #beauty #rituals #elegance #mirelle",
        "Travel adventures don't need to be far to be magical. A new café, a different street, a slower pace — explore close to home. Share this with a travel buddy! 🗺️ #travel #adventure #explore #local #mirelle",
        "Elegant outfits start with how you feel. When I dress with intention, my whole day lifts. Try it tomorrow and see. Double tap if you agree! 👗 #fashion #outfit #elegance #style #mirelle",
        "Soft glam is my kind of evening look — glowing skin, a warm eye, a confident smile. Save this for your next date night! 🌙 #beauty #makeup #glam #eveninglook #mirelle",
        "The art of living well is noticing beauty everywhere. Flowers on the table, a handwritten note, golden hour light. Comment your favorite little moment! 🌷 #lifestyle #beautyinthelittlethings #mindful #mirelle",
        "Pack light, look chic. A few versatile pieces and thoughtful accessories take you anywhere in style. Like if you want a packing guide! 🧳 #travel #packingtips #style #travelwardrobe #mirelle",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "elegant and refined — make viewers want to embrace timeless style",
        "warm and personal — share real moments from a beautiful everyday life",
        "inspiring and creative — celebrate confidence and self-expression through fashion",
        "travel-loving — emphasise escapes, adventures, and discovering beauty in new places",
        "calm and mindful — emphasise slow living, self-care, and the little moments",
        "glamorous yet effortless — show how elegance can be easy and natural",
        "uplifting and confident — encourage viewers to feel beautiful in their own skin",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Mirelle'. "
        f"A space dedicated to timeless fashion, beauty, travel, and the little moments that make life beautiful. From peaceful countryside escapes and elegant outfits to travel adventures and everyday inspiration, Mirelle shares a lifestyle built around confidence, creativity, and effortless elegance. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if this inspired your style! Comment your favorite look below! Share this with a friend who loves fashion! Follow Mirelle for daily fashion, beauty, and travel inspiration!"
        f"Include relevant hashtags in ALL LOWERCASE such as #fashion #beauty #travel #style #outfit #elegance #countryside #lifestyle #mirelle. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["fashion", "beauty", "travel", "style", "outfit", "elegance", "countryside", "lifestyle", "mirelle", "ootd", "travelvlog", "skincare", "selfcare", "inspiration"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
