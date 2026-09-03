// Workflow: Analyze Trip Reviews
db.TripReviews.aggregate([
  {
    $facet: {
      
      // 1. Rating distribution
      // Each review is counted once.
      "rating_distribution": [
        {
          $group: {
            _id: "$rating",
            count: { $sum: 1 }
          }
        },
        {
          $sort: { "_id": -1 }
        }
      ],

      // 2. Most frequent feedback tags
      // Unwind the array so each tag can be counted separately.
      "common_feedback": [
        {
          $unwind: "$feedback_tags"
        },
        {
          $group: {
            _id: "$feedback_tags",
            total_occurrences: { $sum: 1 }
          }
        },
        {
          $sort: { total_occurrences: -1 }
        },
        {
          $limit: 10
        }
      ],

      // 3. Overall average rating
      "overall_average_rating": [
        {
          $group: {
            _id: null,
            average_rating: { $avg: "$rating" }
          }
        },
        {
          $project: {
            _id: 0,
            average_rating: 1
          }
        }
      ]
    }
  }
]);
