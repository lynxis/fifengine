/***************************************************************************
 *   Copyright (C) 2005-2008 by the FIFE team                              *
 *   http://www.fifengine.de                                               *
 *   This file is part of FIFE.                                            *
 *                                                                         *
 *   FIFE is free software; you can redistribute it and/or modify          *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA              *
 ***************************************************************************/

#ifndef FIFE_INSTANCE_H
#define FIFE_INSTANCE_H

// Standard C++ library includes
#include <vector>

// 3rd party library includes

// FIFE includes
// These includes are split up in two parts, separated by one empty line
// First block: files included from the FIFE root src directory
// Second block: files included from the same folder
#include "model/metamodel/object.h"
#include "model/metamodel/abstractvisual.h"

#include "location.h"


namespace FIFE {

	class Layer;
	class Action;
	class Instance;
	class ActionInfo;
	class SayInfo;
	class TimeProvider;

	class InstanceActionListener {
	public:
		virtual ~InstanceActionListener() {};
		virtual void onInstanceActionFinished(Instance* instance, Action* action) = 0;
	};

	enum InstanceChangeType {
		ICHANGE_NO_CHANGES = 0x0000,
		ICHANGE_LOC = 0x0001,
		ICHANGE_FACING_LOC = 0x0002,
		ICHANGE_SPEED = 0x0004,
		ICHANGE_ACTION = 0x0008,
		ICHANGE_TIME_MULTIPLIER = 0x0010,
		ICHANGE_SAYTEXT = 0x0020,
	};
	typedef unsigned int InstanceChangeInfo;
	
	class InstanceChangeListener {
	public:
		virtual ~InstanceChangeListener() {};
		virtual void onInstanceChanged(Instance* instance, InstanceChangeInfo info) = 0;
	};
	
	/**
	 *  An Instance is an "instantiation" of an Object at a Location.
	 */
	class Instance : public AttributedClass {
	public:

		/** Constructor
		 * Instances are created by calling addInstance from layer, thus
		 * this method should really be called only by layer or test code
		 */
		Instance(Object* object, const Location& location, const std::string& identifier="");

		/** Destructor
		 */
		virtual ~Instance();

		/** Gets object where this instance is instantiated from
		 */
		Object* getObject() { return m_object; }

		/** Sets location of the instance
		 *  @param loc new location
		 */
		void setLocation(const Location& loc);

		/** Gets current location of instance
		 *  @note does not return const Location&, since swig wont be const correct
		 *  @return current location
		 */
		Location getLocation() const { return m_location; }
		
		/** Gets reference of current location of instance
		 *  @return reference to current location
		 */
		Location& getLocationRef() { return m_location; }
		
		/** Gets movement target in case instance is moving. In case not, returns current location
		 *  To move target location, call move-method
		 *  @see move
		 *  @note does not return const Location&, since swig wont be const correct
		 *  @return Movement target location
		 */
		Location getTargetLocation() const;
		
		/** Sets the direction where instance is heading. Useful e.g. with static
		 * instances which don't "move" or "act"
		 */
		void setFacingLocation(const Location& loc);
		
		/** Returns the direction where instance is heading
		*  @note does not return const Location&, since swig wont be const correct
		 * @return the direction of instance.
		 */
		Location getFacingLocation() const;
		
		/** Returns reference to the direction where instance is heading
		 * Note: if instance didn't previously hadn't defined facing location
		 * (e.g. by movement or setFacingLocation), method creates the location
		 * thus increasing memory consumption.
		 * @return reference to the direction of instance.
		 */
		Location& getFacingLocationRef();
		
		/** Adds new instance action listener
		 * @param listener to add
		 */
		void addActionListener(InstanceActionListener* listener);

		/** Removes associated instance action listener
		 * @param listener to remove
		 */
		void removeActionListener(InstanceActionListener* listener);

		/** Adds new instance change listener
		 * @param listener to add
		 */
		void addChangeListener(InstanceChangeListener* listener);

		/** Removes associated instance change listener
		 * @param listener to remove
		 */
		void removeChangeListener(InstanceChangeListener* listener);
		
		/** Gets the currently active action. This is owned by
		 *  the instance's object, so don't delete it!
		 * @return current action, NULL in case there is none
		 */
		Action* getCurrentAction() const;

		/** Gets the speed in case instance is moving
		 *  otherwise returns 0
		 * @return instance speed. Value 1 means distance 1 in layer coordinates / second
		 */
		double getMovementSpeed() const;

		/** Gets the time in milliseconds how long action has been active
		 *  In case there is no current action, returns -1
		 * @return action runtime
		 */
		int getActionRuntime() const;

		/** Performs given named action to the instance. While performing the action
		 *  moves instance to given target with given speed
		 *  @param action_name name of the action
		 *  @param target place where to move this instance
		 *  @param speed speed used for movement. Units = distance 1 in layer coordinates per second
		 */
		void move(const std::string& action_name, const Location& target, const double speed);

		/** Performs given named action to the instance. Performs no movement
		 *  @param action_name name of the action
		 *  @param direction coordinates for cell towards instance is heading to when performing the action
		 *  @param repeating in case true, keeps repeating this action
		 */
		void act(const std::string& action_name, const Location& direction, bool repeating=false);

		/** Causes instance to "say" given text (shown on screen next to the instance)
		 *  @param text text to say. If "" given, clear the text
		 *  @param duration duration to show the text (in ms). If 0, shows forever
		 */
		void say(const std::string& text, unsigned int duration=0);

		/** Performs given named action to the instance. While performing the action
		 *  follows given isntance with given speed
		 *  @param action_name name of the action
		 *  @param leader followed instance
		 *  @param speed speed used for movement. Units = distance 1 in layer coordinates per second
		 */
		void follow(const std::string& action_name, Instance* leader, const double speed);

		/** Returns pointer to currently set saytext. In case no text is set, returns NULL
		 */
		const std::string* getSayText() const;

		/** Updates the instance related to the current action
		 * @param curticks current tick count of the system
		 * @note call this only once in engine update cycle, so that tracking between
		 *  current position and previous position keeps in sync.
		 * @returns marked changes
		 */
		InstanceChangeInfo update(unsigned int curticks=0);
		
		/** Sets visualization to be used. Transfers ownership.
		 */
		void setVisual(AbstractVisual* visual) { m_visual = visual; }
		
		/** Gets used visualization
		 */
		template<typename T> T* getVisual() const { return reinterpret_cast<T*>(m_visual); }
		
		/** Sets speed for the map. See Model::setTimeMultiplier.
		*/
		void setTimeMultiplier(float multip);
		
		/** Gets instance speed. @see setTimeMultiplier.
		*/
		float getTimeMultiplier();
		
		/** Gets instance speed, considering also model and map speeds. @see setTimeMultiplier.
		*/
		float getTotalTimeMultiplier();
		
		/** Refreshes instance e.g. in case location is updated directly (not via setLocation)
		 * In this case e.g. instance's master time provider is changed, so it needs to be updated
		 */
		void refresh();

		/** Returns a bitmask of changes since previous update
		 */
		inline InstanceChangeInfo getChangeInfo();

		std::vector<std::string> listFields() const;
		const std::string& get(const std::string& field);

	private:
		class InstanceActivityCache {
		public:
			InstanceActivityCache(Instance& source);
			~InstanceActivityCache();
			void update(Instance& source);
			
			Location m_location;
			Location m_facinglocation;
			Action* m_action; // note! might become invalid, only used for address comparison
			double m_speed;
			float m_timemultiplier;
			std::string m_saytxt;
			InstanceChangeInfo m_changeinfo;
			
			// -- fields related to activity starting here --
			// instance listeners stored here, in case you subscribe to listen this instance, you expect it to be changed
			std::vector<InstanceActionListener*> m_actionlisteners;
			std::vector<InstanceChangeListener*> m_changelisteners;
			// action information, allocated when actions are bind
			ActionInfo* m_actioninfo;
			// text to say + duration, NULL if nothing
			SayInfo* m_sayinfo;
			// time scaler for this instance
			TimeProvider* m_timeprovider;
		};
		// cache storing changes since previous round. Just a pointer so that static instances 
		//  (e.g. tiles) don't consume futile space
		InstanceActivityCache* m_activitycache;
		
		// object where instantiated from
		Object* m_object;
		// current location
		Location m_location;
		// current facing location. Just a pointer to save space e.g. on tiles
		Location* m_facinglocation;
		// instance visualization
		AbstractVisual* m_visual;
		
		Instance(const Instance&);
		Instance& operator=(const Instance&);
		// Finalize current action
		void finalizeAction();
		// Initialize action for use
		void initalizeAction(const std::string& action_name);
		// Moves instance. Returns true if finished
		bool process_movement();
		// Calculates movement based current location and speed
		void calcMovement();
		// rebinds time provider based on new location
		void bindTimeProvider();
		// called when instance has been changed. Causes instance to create InstanceActivityCache
		void initializeChanges();
	};

	inline InstanceChangeInfo Instance::getChangeInfo() {
		if (m_activitycache) {
			return m_activitycache->m_changeinfo;
		}
		return ICHANGE_NO_CHANGES;
	}
} // FIFE

#endif
