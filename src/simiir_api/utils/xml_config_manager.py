"""XML configuration file manager for simIIR"""

from typing import List, Optional
from lxml import etree


class XMLConfigManager:
    """Manager for simIIR XML configuration files"""
    
    def __init__(self, xml_content: str):
        """Initialize with XML content string"""
        self.tree = etree.fromstring(xml_content.encode('utf-8'))
    
    def set_users(self, user_ids: List[str]):
        """Set the list of users in the configuration"""
        # Find users element
        users_elem = self.tree.find('.//users')
        
        if users_elem is not None:
            # Clear existing users
            users_elem.clear()
            users_elem.tag = 'users'
            
            # Add new users
            for user_id in user_ids:
                user_elem = etree.SubElement(users_elem, 'user')
                user_elem.text = user_id
    
    def set_topics(self, topic_ids: List[str]):
        """Set the list of topics in the configuration"""
        # Find topics element
        topics_elem = self.tree.find('.//topics')
        
        if topics_elem is not None:
            # Clear existing topics
            topics_elem.clear()
            topics_elem.tag = 'topics'
            
            # Add new topics
            for topic_id in topic_ids:
                topic_elem = etree.SubElement(topics_elem, 'topic')
                topic_elem.text = topic_id
    
    def set_output_directory(self, output_dir: str):
        """Set the output directory in the configuration"""
        # Find output element
        output_elem = self.tree.find('.//output')
        
        if output_elem is not None:
            # Update or create directory attribute/element
            dir_attr = output_elem.get('directory')
            if dir_attr is not None:
                output_elem.set('directory', output_dir)
            else:
                dir_elem = output_elem.find('directory')
                if dir_elem is not None:
                    dir_elem.text = output_dir
                else:
                    # Create new directory element
                    dir_elem = etree.SubElement(output_elem, 'directory')
                    dir_elem.text = output_dir
    
    def get_users(self) -> List[str]:
        """Get list of users from configuration"""
        users = []
        users_elem = self.tree.find('.//users')
        
        if users_elem is not None:
            for user_elem in users_elem.findall('user'):
                if user_elem.text:
                    users.append(user_elem.text.strip())
        
        return users
    
    def get_topics(self) -> List[str]:
        """Get list of topics from configuration"""
        topics = []
        topics_elem = self.tree.find('.//topics')
        
        if topics_elem is not None:
            for topic_elem in topics_elem.findall('topic'):
                if topic_elem.text:
                    topics.append(topic_elem.text.strip())
        
        return topics
    
    def to_string(self) -> str:
        """Convert back to XML string"""
        return etree.tostring(
            self.tree,
            encoding='unicode',
            pretty_print=True,
        )
    
    def validate(self) -> bool:
        """Basic validation of the XML structure"""
        # Check for required elements
        required_elements = ['users', 'topics', 'output']
        
        for elem_name in required_elements:
            if self.tree.find(f'.//{elem_name}') is None:
                return False
        
        return True

